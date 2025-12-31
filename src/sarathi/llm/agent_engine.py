import json
import time
from sarathi.llm.call_llm import call_llm_model
from sarathi.llm.tools import registry

class AgentEngine:
    def __init__(self, agent_name, system_prompt=None, tools=None, tool_confirmation_callback=None):
        from sarathi.config.config_manager import config
        self.agent_name = agent_name
        
        # If no explicit system_prompt provided, try loading from config
        if system_prompt is None:
            system_prompt = config.get(f"prompts.{agent_name}")
            
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_confirmation_callback = tool_confirmation_callback
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def run(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        
        while True:
            # Current call_llm_model doesn't support tool history directly, 
            # we need to modify it or implement the loop here using the same logic.
            # For now, let's assume we need to extend call_llm_model to handle tools.
            response = self._call_llm()
            
            choices = response.get("choices", [])
            if not choices:
                return "Error: No choices returned from LLM."
                
            choice = choices[0]
            if not choice:
                return "Error: Empty choice returned from LLM."
                
            message = choice.get("message", {})
            if not message:
                return "Error: No message in LLM choice."
            
            tool_calls = message.get("tool_calls")
            if tool_calls:
                self.messages.append(message)
                for tool_call in tool_calls:
                    if not isinstance(tool_call, dict):
                        continue
                        
                    func_info = tool_call.get("function")
                    if not func_info:
                        continue
                        
                    func_name = func_info.get("name")
                    func_args = func_info.get("arguments")
                    
                    if not func_name:
                        continue
                    
                    print(f"Agent {self.agent_name} is calling tool: {func_name}")
                    
                    # Check permission if callback provided
                    if self.tool_confirmation_callback:
                        if not self.tool_confirmation_callback(func_name, func_args):
                            print(f"Tool execution denied by user: {func_name}")
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.get("id"),
                                "name": func_name,
                                "content": "Tool execution was denied by the user."
                            })
                            continue

                    result = registry.call_tool(func_name, func_args)
                    
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": func_name,
                        "content": str(result)
                    })
                # Continue loop to send tool results back to LLM
                continue
            else:
                # No tool calls, we have a final answer
                return message.get("content")

    def _call_llm(self):
        # We need a version of call_llm_model that accepts full message history and tools
        # Let's adapt call_llm_model or import it and use its logic
        from sarathi.llm.call_llm import get_agent_config
        from sarathi.config.config_manager import config
        from sarathi.utils.usage import usage_tracker
        import requests

        agent_conf = get_agent_config(self.agent_name)
        provider_name = agent_conf.get("provider", "openai")
        provider_conf = config.get_provider_config(provider_name)
        base_url = provider_conf.get("base_url")
        url = f"{base_url.rstrip('/')}/chat/completions"
        api_key = provider_conf.get("api_key")
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": agent_conf.get("model", "gpt-4o-mini"),
            "messages": self.messages,
            "tools": registry.get_tool_definitions() if self.tools else None,
            "temperature": agent_conf.get("temperature", 0.7),
        }
        
        # Remove tools if empty
        if not body["tools"]:
            del body["tools"]
            
        if config.get("core.debug"):
            from sarathi.utils.formatters import format_yellow
            print(f"\n{format_yellow('--- DEBUG: LLM REQUEST BODY ---')}")
            print(json.dumps(body, indent=2))
            print(f"{format_yellow('--- END DEBUG ---')}\n")

        start_time = time.time()
        res = requests.post(
            url, 
            headers=headers, 
            json=body, 
            timeout=config.get("core.timeout", 30),
            verify=config.get("core.verify_ssl", True)
        )
        res.raise_for_status()
        end_time = time.time()
        
        data = res.json()
        
        # Record usage
        usage = data.get("usage")
        usage_tracker.record_call(end_time - start_time, usage)
        
        return data
