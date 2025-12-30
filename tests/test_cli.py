import pytest
from unittest.mock import patch, MagicMock
from sarathi.cli.cli_handler import parse_cmd_args, main
from sarathi.cli.registry import CLI_REGISTRY

def test_parse_args_help():
    with patch("sys.stdout") as mock_stdout, patch("sys.stderr") as mock_stderr:
        with pytest.raises(SystemExit):
             with patch("sys.argv", ["sarathi", "--help"]):
                 parse_cmd_args()

def test_parse_args_ask():
    with patch("sys.argv", ["sarathi", "ask", "-q", "hello"]):
        args = parse_cmd_args()
        assert args.op == "ask"
        assert args.question == "hello"

def test_registry_structure():
    assert "git" in CLI_REGISTRY
    assert "ask" in CLI_REGISTRY
    assert CLI_REGISTRY["git"]["custom_setup"] is True
    
def test_main_dispatch():
    # Mock the handler for the 'ask' command to ensure it gets called
    with patch("sys.argv", ["sarathi", "ask", "-q", "hello"]):
        # We need to mock importlib because main() does dynamic imports
        mock_module = MagicMock()
        mock_handler = MagicMock()
        setattr(mock_module, "execute_cmd", mock_handler)
        
        with patch("importlib.import_module", return_value=mock_module) as mock_import:
            main()
            
            # Verify module import
            mock_import.assert_called_with(CLI_REGISTRY["ask"]["module"])
            
            # Verify handler called
            mock_handler.assert_called_once()
            args = mock_handler.call_args[0][0]
            assert args.question == "hello"
