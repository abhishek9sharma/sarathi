import json
from sarathi.llm.call_llm import call_llm_model
from sarathi.llm.tools import registry

class AgentEngine:
    def __init__(self, agent_name, system_prompt=None, tools=None):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tools = tools or []
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
            
            # Check for tool calls in response
            # Assuming OpenAI format for tool calls
            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})
            
            if message.get("tool_calls"):
                self.messages.append(message)
                for tool_call in message["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    func_args = tool_call["function"]["arguments"]
                    
                    print(f"Agent {self.agent_name} is calling tool: {func_name}")
                    result = registry.call_tool(func_name, func_args)
                    
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
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
        import time

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

        start_time = time.time()
        res = requests.post(url, headers=headers, json=body, timeout=config.get("core.timeout", 30))
        res.raise_for_status()
        end_time = time.time()
        
        data = res.json()
        
        # Record usage
        usage = data.get("usage")
        usage_tracker.record_call(end_time - start_time, usage)
        
        return data
