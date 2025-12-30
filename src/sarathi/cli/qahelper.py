from sarathi.llm.agent_engine import AgentEngine
from sarathi.llm.prompts import prompt_dict
from sarathi.llm.tool_library import registry # Ensure tools are registered

def execute_cmd(args):
    """Execute a command.

    Args:
        args: A dictionary containing the command arguments.

    Returns:
        None
    """
    question_asked = args.question
    
    # Initialize Agent with tools
    agent = AgentEngine(
        agent_name="qahelper",
        system_prompt=prompt_dict["qahelper"]["system_msg"],
        tools=list(registry.tools.keys())
    )
    
    print("Agent is thinking (and may use tools)...")
    answer = agent.run(question_asked)
    print("\n" + answer)
