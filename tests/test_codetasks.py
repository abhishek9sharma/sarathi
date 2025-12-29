import pytest
import ast
import tempfile
import os
from unittest.mock import patch, MagicMock
from sarathi.code.codetasks import CodeTransformer

# Sample Python code for testing
SAMPLE_CODE = '''
def hello_world():
    print("Hello")
    
class MyClass:
    def method_one(self, arg1):
        return arg1 * 2
    
    def method_two(self):
        """Existing docstring"""
        pass
'''

SAMPLE_CODE_WITH_DOCSTRINGS = '''
def hello_world():
    """Says hello"""
    print("Hello")
'''

@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(SAMPLE_CODE)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_code_transformer_init(temp_python_file):
    ct = CodeTransformer(temp_python_file)
    assert ct.file_path == temp_python_file  # Note: it's file_path not filepath
    assert ct.dosctring_prompt == "update_docstrings"

def test_get_ast(temp_python_file):
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    assert tree is not None
    assert isinstance(tree, ast.Module)

def test_find_methods(temp_python_file):
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    methods = ct.find_methods(tree)
    
    # Should find: hello_world, method_one, method_two
    assert len(methods) >= 3
    
    # Check structure
    for method in methods:
        assert isinstance(method, ast.FunctionDef)

def test_check_existing_docstring(temp_python_file):
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    methods = ct.find_methods(tree)
    
    # Find method_two which has a docstring
    method_two = next((m for m in methods if m.name == 'method_two'), None)
    assert method_two is not None
    assert ast.get_docstring(method_two) == "Existing docstring"
    
    # Find hello_world which doesn't have a docstring
    hello_world = next((m for m in methods if m.name == 'hello_world'), None)
    assert hello_world is not None
    assert ast.get_docstring(hello_world) is None

@patch('sarathi.code.codetasks.call_llm_model')
def test_update_docstrings(mock_llm, temp_python_file):
    # Mock LLM response
    mock_llm.return_value = "Generated docstring for method"
    
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    methods = ct.find_methods(tree)
    
    ct.update_docstrings(methods)
    
    # Verify LLM was called for methods without docstrings
    assert mock_llm.called

@patch('sarathi.code.codetasks.call_llm_model')
def test_update_docstrings_skip_existing(mock_llm, temp_python_file):
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    methods = ct.find_methods(tree)
    
    # Find method with existing docstring
    method_two = next((m for m in methods if m.name == 'method_two'), None)
    
    # Update with overwrite_existing=False (default)
    ct.update_docstrings([method_two], overwrite_existing=False)
    
    # LLM should NOT be called for methods with existing docstrings
    mock_llm.assert_not_called()

@patch('sarathi.code.codetasks.call_llm_model')
def test_update_docstrings_overwrite(mock_llm, temp_python_file):
    mock_llm.return_value = "New docstring"
    
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    methods = ct.find_methods(tree)
    
    # Find method with existing docstring
    method_two = next((m for m in methods if m.name == 'method_two'), None)
    
    # Update with overwrite_existing=True
    ct.update_docstrings([method_two], overwrite_existing=True)
    
    # LLM SHOULD be called even for methods with existing docstrings
    assert mock_llm.called

@patch('sarathi.code.codetasks.format_code')
def test_update_code(mock_format, temp_python_file):
    mock_format.return_value = "formatted code"
    
    ct = CodeTransformer(temp_python_file)
    ct.update_code("new code")
    
    # Verify format_code was called
    mock_format.assert_called_once_with("new code")
    
    # Verify file was written
    with open(temp_python_file, 'r') as f:
        content = f.read()
    assert content == "formatted code"

@patch('sarathi.code.codetasks.call_llm_model')
@patch('sarathi.code.codetasks.format_code')
def test_transform_code(mock_format, mock_llm, temp_python_file):
    mock_llm.return_value = "Test docstring"
    mock_format.side_effect = lambda x: x  # Return input unchanged
    
    ct = CodeTransformer(temp_python_file)
    ct.transform_code(op="update_docstrings")
    
    # Verify LLM was called
    assert mock_llm.called
    
    # Verify format_code was called
    assert mock_format.called
    
    # Verify file was updated
    with open(temp_python_file, 'r') as f:
        content = f.read()
    assert len(content) > 0

def test_format_node_with_new_docstring(temp_python_file):
    ct = CodeTransformer(temp_python_file)
    tree = ct.get_ast()
    methods = ct.find_methods(tree)
    
    method = methods[0]
    new_docstring = "Test docstring"
    
    node = ct.format_node_with_new_docstring(new_docstring, method)
    
    assert isinstance(node, ast.Expr)
    assert isinstance(node.value, ast.Str)
