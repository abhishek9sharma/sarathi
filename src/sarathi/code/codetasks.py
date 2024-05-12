import ast
import subprocess

import astor

from sarathi.llm.call_llm import call_llm_model
from sarathi.llm.prompts import prompt_dict
from sarathi.utils.formatters import format_code


class CodeTransformer:
    def __init__(self, file_path):
        """Initializes the class with the provided file path.

        Args:
            file_path: The path to the file.

        Returns:
            None.
        """
        self.file_path = file_path
        self.dosctring_prompt = "update_docstrings"

    def get_ast(self):
        """Parse the content of a file and return the abstract syntax tree (AST).

        Returns:
            The abstract syntax tree (AST) generated from the content of the file.
        """
        with open(self.file_path, "r") as file:
            code = file.read()
        return ast.parse(code)

    def find_methods(self, tree):
        """Find all the methods in the given abstract syntax tree.

        Args:
            self: The instance of the class.
            tree: The abstract syntax tree to search for methods.

        Returns:
            A list of method nodes found in the abstract syntax tree.
        """
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node)
        return methods

    def format_node_with_new_docstring(self, new_docstring, method):
        """
        Formats a node with a new docstring.

        Args:
            new_docstring: The new docstring to be formatted.
            method: The method to which the new docstring will be added.

        Returns:
            The new docstring node after formatting.
        """
        indentation = method.body[0].col_offset if method.body else 0
        new_docstring = new_docstring.replace('"""', "")
        new_docstring = new_docstring.replace("'", "")
        new_docstring_node = ast.Expr(
            value=ast.Str(new_docstring), lineno=method.lineno, col_offset=indentation
        )
        return new_docstring_node

    def update_docstrings(self, methods, overwrite_existing=False):
        """Update docstrings for the given methods.

        Args:
            methods: A list of methods whose docstrings need to be updated.
            overwrite_existing: A boolean flag indicating whether to overwrite existing docstrings. Default is False.

        Returns:
            None.
        """
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
            except Exception as e:
                print(f"{e}")

    def transform_code(self, op="update_docstrings"):
        """Transforms the code based on the specified operation.

        Args:
            op: The operation to be performed. Default value is update_docstrings.

        Returns:
            None
        """
        tree = self.get_ast()
        if op == "update_docstrings":
            methods = self.find_methods(tree)
            self.update_docstrings(methods)
        modified_source = astor.to_source(tree)
        self.update_code(modified_source)

    def update_code(self, updated_code):
        """Update the code in the file with the provided updated code.

        Args:
            updated_code: The updated code that needs to be written to the file.

        Returns:
            None
        """
        formatted_code = format_code(updated_code)
        with open(self.file_path, "w") as f:
            f.write(formatted_code)
