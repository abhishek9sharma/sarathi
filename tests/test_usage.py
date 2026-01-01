import pytest
from sarathi.utils.usage import UsageTracker

def test_usage_tracker_accumulation():
    tracker = UsageTracker()
    tracker.record_call(1.0, {"prompt_tokens": 10, "completion_tokens": 5})
    tracker.record_call(2.0, {"prompt_tokens": 20, "completion_tokens": 10})
    
    assert tracker.total_calls == 2
    assert tracker.total_time_seconds == 3.0
    assert tracker.total_input_tokens == 30
    assert tracker.total_output_tokens == 15

def test_usage_tracker_different_keys():
    tracker = UsageTracker()
    # Test input_tokens/output_tokens (Anthropic style)
    tracker.record_call(1.0, {"input_tokens": 10, "output_tokens": 5})
    assert tracker.total_input_tokens == 10
    assert tracker.total_output_tokens == 5
    
    # Test total_tokens fallback
    tracker.record_call(1.0, {"total_tokens": 20, "completion_tokens": 8})
    assert tracker.total_input_tokens == 22 # 10 + (20-8)
    assert tracker.total_output_tokens == 13 # 5 + 8

def test_usage_tracker_reset():
    tracker = UsageTracker()
    tracker.record_call(1.0, {"prompt_tokens": 10})
    tracker.reset()
    assert tracker.total_calls == 0
    assert tracker.total_input_tokens == 0
    assert tracker.total_time_seconds == 0.0

def test_usage_tracker_summary():
    tracker = UsageTracker()
    tracker.record_call(2.0, {"prompt_tokens": 100, "completion_tokens": 50})
    summary = tracker.get_summary()
    assert "Total LLM Calls    : 1" in summary
    assert "Total Input Tokens : 100" in summary
    assert "Total Output Tokens: 50" in summary
    assert "Output TPS (avg)   : 25.00" in summary # 50 / 2.0
