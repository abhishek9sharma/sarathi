import time
from typing import Dict, List, Optional

class UsageTracker:
    """
    Globally tracks token usage and request times across the CLI execution.
    """
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        self.total_time_seconds = 0.0

    def record_call(self, time_seconds: float, usage: Optional[Dict[str, int]] = None):
        """
        Records statistics from a single LLM call.
        """
        self.total_calls += 1
        self.total_time_seconds += time_seconds
        
        if usage:
            self.total_input_tokens += usage.get("prompt_tokens", 0)
            self.total_output_tokens += usage.get("completion_tokens", 0)

    def get_summary(self) -> str:
        """
        Generates a summary string of the usage statistics.
        """
        if self.total_calls == 0:
            return ""

        total_tokens = self.total_input_tokens + self.total_output_tokens
        tps = self.total_output_tokens / self.total_time_seconds if self.total_time_seconds > 0 else 0
        
        summary = [
            "\n" + "="*40,
            "📊 LLM USAGE STATISTICS",
            "="*40,
            f"Total LLM Calls    : {self.total_calls}",
            f"Total Input Tokens : {self.total_input_tokens}",
            f"Total Output Tokens: {self.total_output_tokens}",
            f"Total Tokens       : {total_tokens}",
            f"Total Time         : {self.total_time_seconds:.2f}s",
            f"Output TPS (avg)   : {tps:.2f} tokens/s",
            "="*40
        ]
        return "\n".join(summary)

# Global instances for tracking
usage_tracker = UsageTracker()
