import ast
import subprocess

import astor

from src.sarathi.llm.call_llm import call_llm_model
from src.sarathi.llm.prompts import prompt_dict
from src.sarathi.utils.formatters import format_code


class CodeTransformer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dosctring_prompt = "update_docstrings"

    def get_ast(self):
        with open(self.file_path, "r") as file:
            code = file.read()
        return ast.parse(code)

    def find_methods(self, tree):
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node)
        return methods

    def format_node_with_new_docstring(self, new_docstring, method):
        indentation = method.body[0].col_offset if method.body else 0
        new_docstring_node = ast.Expr(
            value=ast.Str(new_docstring.replace('"""', "")),
            lineno=method.lineno,
            col_offset=indentation,
        )
        return new_docstring_node

    def update_docstrings(self, methods, overwrite_existing=False):
        for method in methods:
            try:
                existing_docstring = ast.get_docstring(method)
                existing_method_code = ast.unparse(method)
                if existing_docstring:
                    if overwrite_existing:
                        new_docstring = call_llm_model(
                            prompt_info=prompt_dict[self.dosctring_prompt],
                            user_msg=existing_method_code,
                            resp_type="text",
                        )
                        new_docstring_node = self.format_node_with_new_docstring(
                            new_docstring, method
                        )
                        method.body.insert(0, new_docstring_node)
                    else:
                        pass
                else:
                    new_docstring = call_llm_model(
                        prompt_info=prompt_dict[self.dosctring_prompt],
                        user_msg=existing_method_code,
                        resp_type="text",
                    )
                    if new_docstring is not None:
                        new_docstring_node = self.format_node_with_new_docstring(
                            new_docstring, method
                        )
                        method.body.insert(0, new_docstring_node)
                        # method.body = new_docstring.body[0].body
            except Exception as e:
                print(f"{e}")

    def transform_code(self, op="update_docstrings"):
        tree = self.get_ast()
        if op == "update_docstrings":
            methods = self.find_methods(tree)
            self.update_docstrings(methods)
        return astor.to_source(tree)

    def update_code(self, updated_code):
        formatted_code = format_code(updated_code)
        with open(self.file_path, "w") as f:
            f.write(formatted_code)
