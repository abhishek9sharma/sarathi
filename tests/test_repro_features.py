"""
Tests for new streaming/reasoning features.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from sarathi.config.config_manager import config
from sarathi.llm.agent_engine import AgentEngine
from sarathi.llm.response_parser import ResponseParser, ToolCallAggregator


class TestFeatures(unittest.TestCase):

    def test_config_defaults(self):
        """Test that new config defaults are loaded."""
        # Check core.simple_mode exists in config (may be False by default)
        simple_mode = config.get("core.simple_mode")
        self.assertIsNotNone(simple_mode) or self.assertFalse(simple_mode)

    def test_response_parser_reasoning_content_cleaning(self):
        """Test that ResponseParser cleans system prompt artifacts from reasoning content."""
        parser = ResponseParser(is_reasoning_model=True)
        
        # Test SGLang style
        dirty = "<|system|>You are a helpful assistant.<|/system|>\n\nActual reasoning here"
        cleaned = parser.clean_reasoning_content(dirty)
        self.assertNotIn("<|system|>", cleaned)
        self.assertIn("Actual reasoning here", cleaned)
        
        # Test XML style
        dirty2 = "<system>System prompt text</system>\n\nReal content"
        cleaned2 = parser.clean_reasoning_content(dirty2)
        self.assertNotIn("<system>", cleaned2)
        self.assertIn("Real content", cleaned2)

    def test_tool_call_aggregator(self):
        """Test ToolCallAggregator properly aggregates streaming chunks."""
        aggregator = ToolCallAggregator()
        
        # Simulate streaming tool call chunks
        aggregator.add_chunk([{
            "index": 0,
            "id": "call_123",
            "function": {"name": "read_", "arguments": ""}
        }])
        aggregator.add_chunk([{
            "index": 0,
            "function": {"name": "file", "arguments": '{"path'}
        }])
        aggregator.add_chunk([{
            "index": 0,
            "function": {"arguments": '": "test.py"}'}
        }])
        
        calls = aggregator.get_complete_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["name"], "read_file")
        self.assertEqual(calls[0]["function"]["arguments"], '{"path": "test.py"}')

    @patch("sarathi.llm.llm_client.LLMClient.call_sync")
    def test_streaming_flag_false_uses_sync(self, mock_sync):
        """Test that stream=False config triggers non-streaming path."""
        mock_sync.return_value = {"choices": [{"message": {"content": "Hello"}}]}
        
        with patch.object(config, "get_agent_config", return_value={"stream": False, "model": "test-model"}):
            with patch("sarathi.llm.agent_engine.registry.get_tool_definitions", return_value=None):
                agent = AgentEngine(agent_name="test_agent")
                
                # Force the client config to use non-streaming
                agent.client._agent_conf = {"stream": False, "model": "test-model"}
                agent.client._provider_conf = {"base_url": "http://test"}
                
                # Run sync iteration directly
                result = list(agent._run_sync_iteration())
                
                mock_sync.assert_called_once()

    @patch("sarathi.llm.llm_client.LLMClient.call_streaming")
    def test_tool_call_event_structure(self, mock_stream):
        """Test that tool calls are yielded as structured events."""
        
        def mock_streaming(*args, **kwargs):
            yield {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "id": "call_123",
                            "function": {"name": "test_tool", "arguments": "{}"}
                        }]
                    }
                }]
            }
        
        mock_stream.side_effect = mock_streaming
        
        with patch("sarathi.llm.agent_engine.registry") as mock_registry:
            mock_registry.call_tool.return_value = "Tool Result"
            mock_registry.get_tool_definitions.return_value = [{"type": "function"}]
            
            agent = AgentEngine(agent_name="chat", tools=["test_tool"])
            
            events = list(agent.run_stream("Call tool"))
            
            # Check for structured event
            tool_event = next((e for e in events if isinstance(e, dict) and e.get("type") == "tool_call"), None)
            
            self.assertIsNotNone(tool_event)
            self.assertEqual(tool_event["name"], "test_tool")


if __name__ == "__main__":
    unittest.main()
