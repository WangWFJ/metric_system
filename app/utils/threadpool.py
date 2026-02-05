import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

from core.config import settings

_executor = ThreadPoolExecutor(max_workers=settings.PANDAS_THREAD_WORKERS)
_semaphore = asyncio.Semaphore(settings.PANDAS_JOB_CONCURRENCY)


async def run_pandas(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    async with _semaphore:
        return await loop.run_in_executor(_executor, functools.partial(func, *args, **kwargs))
