"""
Parallel diff analyzer for generating comprehensive commit messages.

Analyzes each file's changes concurrently using async LLM calls,
with smart batching to optimize API costs.
"""

import asyncio
import subprocess
from typing import Dict, List, Optional, Tuple

from sarathi.config.config_manager import config
from sarathi.llm.async_llm import AsyncLLMClient
from sarathi.utils.formatters import clean_llm_response


class ParallelDiffAnalyzer:
    """
    Analyzes git diffs per-file in parallel with cost-efficient batching.

    Uses a fan-out/fan-in pattern:
    1. Fan-out: Analyze each file (or batch of small files) concurrently
    2. Fan-in: Coordinate results into a unified commit message
    """

    # Cost optimization thresholds
    SMALL_FILE_THRESHOLD = 500  # chars - batch files smaller than this
    MAX_BATCH_SIZE = 3  # files per batch
    MAX_CONCURRENT = 4  # parallel LLM calls
    MAX_DIFF_CHARS = 2000  # truncate large diffs

    def __init__(self, agent_name: str = "commit_generator"):
        """
        Initialize the analyzer.

        Args:
            agent_name: Agent configuration to use for LLM calls.
        """
        self.agent_name = agent_name
        self.client = AsyncLLMClient(agent_name)

        # Load prompts from config
        self.file_prompt = config.get(
            "prompts.file_analysis",
            """Analyze this git diff and provide a 1-line summary (max 15 words).
Focus on: what changed and why it matters. Be specific about the change.

{diff}""",
        )

        self.coordinator_prompt = config.get(
            "prompts.commit_coordination",
            """Generate a git commit message from these file summaries.

Rules:
- First line: imperative mood summary, max 50 chars (e.g., "Add user authentication")
- Blank line after first line
- Bullet points for each significant change
- Max 72 chars per line
- Be concise but informative

File changes:
{summaries}""",
        )

    # --- Git Operations ---

    def get_staged_files(self) -> List[str]:
        """
        Get list of staged file paths.

        Returns:
            List of file paths with staged changes.
        """
        result = subprocess.run(
            ["git", "diff", "--staged", "--name-only"], capture_output=True, text=True
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    def get_file_diff(self, filepath: str) -> str:
        """
        Get diff for a single file, truncated for cost efficiency.

        Args:
            filepath: Path to the file.

        Returns:
            The diff output, truncated if too large.
        """
        result = subprocess.run(
            ["git", "diff", "--staged", "--", filepath], capture_output=True, text=True
        )
        diff = result.stdout
        if len(diff) > self.MAX_DIFF_CHARS:
            diff = diff[: self.MAX_DIFF_CHARS] + "\n... (truncated for brevity)"
        return diff

    # --- Batching Logic ---

    def create_batches(self, file_diffs: Dict[str, str]) -> List[List[Tuple[str, str]]]:
        """
        Group small files into batches to reduce API calls.

        Large files get their own batch, small files are grouped together.

        Args:
            file_diffs: Dict mapping filepath to diff content.

        Returns:
            List of batches, each batch is a list of (filepath, diff) tuples.
        """
        small_files: List[Tuple[str, str]] = []
        batches: List[List[Tuple[str, str]]] = []

        for filepath, diff in file_diffs.items():
            if len(diff) < self.SMALL_FILE_THRESHOLD:
                small_files.append((filepath, diff))
                if len(small_files) >= self.MAX_BATCH_SIZE:
                    batches.append(small_files[:])
                    small_files = []
            else:
                # Large files get their own batch
                batches.append([(filepath, diff)])

        # Don't forget remaining small files
        if small_files:
            batches.append(small_files)

        return batches

    # --- Analysis ---

    async def analyze_batch(
        self, batch: List[Tuple[str, str]], semaphore: asyncio.Semaphore
    ) -> Dict:
        """
        Analyze a batch of file diffs with a single LLM call.

        Args:
            batch: List of (filepath, diff) tuples.
            semaphore: Semaphore for concurrency control.

        Returns:
            Dict with 'files', 'summary', and 'error' keys.
        """
        async with semaphore:
            if len(batch) == 1:
                filepath, diff = batch[0]
                prompt = self.file_prompt.format(diff=diff)
            else:
                # Combine small files into one prompt
                combined = "\n---\n".join(f"File: {fp}\n{diff}" for fp, diff in batch)
                prompt = self.file_prompt.format(diff=combined)

            messages = [{"role": "user", "content": prompt}]

            try:
                summary = await self.client.complete(messages, max_tokens=100)
                return {
                    "files": [fp for fp, _ in batch],
                    "summary": summary.strip(),
                    "error": None,
                }
            except Exception as e:
                return {
                    "files": [fp for fp, _ in batch],
                    "summary": None,
                    "error": str(e),
                }

    async def coordinate_message(self, results: List[Dict]) -> str:
        """
        Merge file summaries into final commit message.

        Args:
            results: List of analysis results from analyze_batch.

        Returns:
            The final commit message.
        """
        # Filter out errors
        valid_results = [r for r in results if r["summary"]]

        if not valid_results:
            # No successful analyses - abort
            return None

        summaries = "\n".join(
            f"- {', '.join(r['files'])}: {r['summary']}" for r in valid_results
        )

        prompt = self.coordinator_prompt.format(summaries=summaries)
        messages = [{"role": "user", "content": prompt}]

        response = await self.client.complete(messages, max_tokens=200)
        return clean_llm_response(response)

    # --- Main Entry Points ---

    async def analyze_all(self) -> str:
        """
        Analyze all staged files in parallel and generate commit message.

        This is the main async entry point.

        Returns:
            The generated commit message.
        """
        files = self.get_staged_files()
        if not files:
            return "No staged changes found."

        print(f"📂 Analyzing {len(files)} file(s)...")

        # Get diffs for all files
        file_diffs = {f: self.get_file_diff(f) for f in files}

        # Create cost-efficient batches
        batches = self.create_batches(file_diffs)
        print(f"📦 Created {len(batches)} batch(es) for parallel analysis")

        # Run analysis in parallel with concurrency limit
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        tasks = [self.analyze_batch(b, semaphore) for b in batches]
        results = await asyncio.gather(*tasks)

        # Report any errors
        errors = [r for r in results if r["error"]]
        if errors:
            for err in errors:
                print(f"⚠️  Error analyzing {err['files']}: {err['error']}")

        # Merge into final message
        print("🔗 Coordinating final commit message...")
        message = await self.coordinate_message(results)

        return message

    async def cleanup(self):
        """Clean up resources."""
        await self.client.close()

    def run(self) -> str:
        """
        Synchronous wrapper for CLI usage.

        Returns:
            The generated commit message.
        """

        async def _run():
            try:
                return await self.analyze_all()
            finally:
                await self.cleanup()

        return asyncio.run(_run())
