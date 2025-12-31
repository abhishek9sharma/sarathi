import pytest
from unittest.mock import patch, MagicMock
from sarathi.cli.cli_handler import parse_cmd_args, main
from sarathi.cli.registry import CLI_REGISTRY
from sarathi.cli.model_cli import execute_cmd as model_execute
from sarathi.cli.config_cli import execute_cmd as config_execute

def test_parse_args_help():
    with patch("sys.stdout") as mock_stdout, patch("sys.stderr") as mock_stderr:
        with pytest.raises(SystemExit):
             with patch("sys.argv", ["sarathi", "--help"]):
                 parse_cmd_args()

def test_parse_args_chat_question():
    with patch("sys.argv", ["sarathi", "chat", "-q", "hello"]):
        # We need to mock chat_cli setup_args as parse_cmd_args calls it
        args = parse_cmd_args()
        assert args.op == "chat"
        assert args.question == "hello"

def test_registry_structure():
    assert "git" in CLI_REGISTRY
    assert "chat" in CLI_REGISTRY
    assert CLI_REGISTRY["git"]["custom_setup"] is True
    
def test_main_dispatch():
    # Mock the handler for the 'chat' command to ensure it gets called
    with patch("sys.argv", ["sarathi", "chat", "-q", "hello"]):
        # We need to mock importlib because main() does dynamic imports
        mock_module = MagicMock()
        mock_handler = MagicMock()
        
        def mock_setup(subparsers, opname):
            parser = subparsers.add_parser(opname)
            if opname == "chat":
                parser.add_argument("-q", "--question")
        
        setattr(mock_module, "execute_cmd", mock_handler)
        setattr(mock_module, "setup_args", mock_setup)
        
        with patch("importlib.import_module", return_value=mock_module) as mock_import:
            main()
            
            # Verify module import
            mock_import.assert_called_with(CLI_REGISTRY["chat"]["module"])
            
            # Verify handler called
            mock_handler.assert_called_once()
            args = mock_handler.call_args[0][0]
            assert args.question == "hello"

def test_model_cli_command():
    from sarathi.config.config_manager import config
    args = MagicMock()
    args.model_name = "new-model"
    args.agent = "chat"
    args.no_save = True
    
    model_execute(args)
    assert config.get("agents.chat.model") == "new-model"

def test_model_cli_show():
    args = MagicMock()
    args.model_name = None
    args.agent = "chat"
    
    with patch("builtins.print") as mock_print:
        model_execute(args)
        # Check if print was called with something containing 'chat' and its model
        mock_print.assert_any_call("Current Model Configuration:")

def test_config_set_cli_command():
    from sarathi.config.config_manager import config
    args = MagicMock()
    args.config_op = "set"
    args.key = "core.timeout"
    args.value = "100"
    args.no_save = True
    
    config_execute(args)
    assert config.get("core.timeout") == 100
    
    args.key = "core.verify_ssl"
    args.value = "false"
    config_execute(args)
    assert config.get("core.verify_ssl") is False
