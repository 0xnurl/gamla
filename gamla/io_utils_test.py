import asyncio
import random

import pytest

import gamla
from gamla import io_utils

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_batch_decorator():
    times_f_called = 0

    @io_utils.batch_calls
    async def slow_identity(inputs):
        nonlocal times_f_called
        times_f_called += 1
        await asyncio.sleep(random.random() * 0.1 * len(inputs))
        return inputs

    inputs = tuple(range(100))
    results = await gamla.apipe(inputs, gamla.amap(slow_identity), tuple)
    assert results == inputs
    assert times_f_called < 5


async def test_batch_decorator_errors():
    times_f_called = 0

    @io_utils.batch_calls
    async def slow_identity_with_errors(inputs):
        nonlocal times_f_called
        times_f_called += 1
        await asyncio.sleep(random.random() * 0.1 * len(inputs))
        if times_f_called > 1:
            raise ValueError
        return inputs

    assert (await gamla.apipe((1,), gamla.amap(slow_identity_with_errors), tuple)) == (
        1,
    )

    with pytest.raises(ValueError):
        await gamla.apipe((1, 2, 3), gamla.amap(slow_identity_with_errors), tuple)

    assert times_f_called == 2


async def test_with_and_without_deduper():
    inputs = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 3)
    called = []

    async def identity_with_spying_and_delay(x):
        await asyncio.sleep(0.4)
        called.append(x)
        return x

    # Without.
    assert inputs == tuple(await gamla.amap(identity_with_spying_and_delay, inputs))

    assert len(called) == len(inputs)

    called[:] = []

    # With.
    assert inputs == tuple(
        await gamla.amap(
            io_utils.queue_identical_calls(identity_with_spying_and_delay), inputs
        )
    )

    unique = frozenset(inputs)
    assert len(called) == len(unique)
    assert frozenset(called) == unique
