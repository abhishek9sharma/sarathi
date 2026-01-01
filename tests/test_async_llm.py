import asyncio
from unittest.mock import MagicMock, patch

import pytest

from sarathi.config.config_manager import config
from sarathi.llm.async_llm import AsyncLLMClient


def test_async_llm_respects_verify_ssl():
    async def run_test():
        # Force disable SSL
        config.set("core.verify_ssl", False, save=False)

        client = AsyncLLMClient()
        try:
            session = await client._get_session()
            assert session.connector._ssl is False
        finally:
            await client.close()

        # Force enable SSL
        config.set("core.verify_ssl", True, save=False)
        client = AsyncLLMClient()
        try:
            session = await client._get_session()
            assert session.connector._ssl is True
        finally:
            await client.close()

    import asyncio

    asyncio.run(run_test())
