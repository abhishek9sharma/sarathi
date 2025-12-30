import inspect
import json
from functools import wraps

class Tool:
    def __init__(self, name, description, func, parameters):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters

    def to_dict(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name=None, description=None):
        def decorator(func):
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or "No description provided."
            
            # Simple parameter inference (can be expanded)
            parameters = {
                "type": "object",
                "properties": {},
                "required": [],
            }
            
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                # Basic inference, could be improved with type hints
                parameters["properties"][param_name] = {
                    "type": "string", # Default to string
                    "description": f"The {param_name} parameter",
                }
                if param.default is inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            self.tools[tool_name] = Tool(tool_name, tool_description, func, parameters)
            return func
        return decorator

    def get_tool_definitions(self):
        return [tool.to_dict() for tool in self.tools.values()]

    def call_tool(self, name, arguments_json):
        if name not in self.tools:
            return f"Error: Tool {name} not found."
        
        try:
            args = json.loads(arguments_json)
            return self.tools[name].func(**args)
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"

# Global registry
registry = ToolRegistry()
