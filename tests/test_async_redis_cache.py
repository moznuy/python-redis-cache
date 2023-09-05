# TODO: A lot of similar code
import asyncio
import uuid

import pytest
import pytest_asyncio
from redis.asyncio import StrictRedis

from redis_cache import AsyncRedisCache

redis_host = "redis-test-host"
async_client = StrictRedis(host=redis_host, decode_responses=True)


@pytest_asyncio.fixture()
async def async_cache():
    await async_client.flushall()
    yield AsyncRedisCache(redis_client=async_client)
    await async_client.connection_pool.disconnect()


async def add_func_async(n1, n2):
    """ Add function
    Add n1 to n2 and return a uuid4 unique verifier. Simulates long async computation

    Returns:
        tuple(int, str(uuid.uuid4))
    """
    await asyncio.sleep(0.1)
    return n1 + n2, str(uuid.uuid4())


@pytest.mark.asyncio
async def test_async_basic_check(async_cache):
    @async_cache.cache()
    async def add_basic(arg1, arg2):
        return await add_func_async(arg1, arg2)

    r_3_4, v_3_4 = await add_basic(3, 4)
    r_3_4_cached, v_3_4_cached = await add_basic(3, 4)
    # Make sure the same cache is used for kwargs
    r_3_4_cached_kwargs, v_3_4_cached_kwargs = await add_basic(arg1=3, arg2=4)
    r_3_4_cached_mix, v_3_4_cached_mix = await add_basic(3, arg2=4)
    r_5_5, v_5_5 = await add_basic(5, 5)

    assert 7 == r_3_4 == r_3_4_cached == r_3_4_cached_kwargs == r_3_4_cached_mix \
           and v_3_4 == v_3_4_cached == v_3_4_cached_kwargs == v_3_4_cached_mix
    assert 10 == r_5_5 and v_5_5 != r_3_4


@pytest.mark.asyncio
async def test_async_ttl(async_cache):
    @async_cache.cache(ttl=1)
    async def add_ttl(arg1, arg2):
        return await add_func_async(arg1, arg2)

    r_1, v_1 = await add_ttl(3, 4)
    r_2, v_2 = await add_ttl(3, 4)
    await asyncio.sleep(2)

    r_3, v_3 = await add_ttl(3, 4)

    assert 7 == r_1 == r_2 == r_3
    assert v_1 == v_2 != v_3