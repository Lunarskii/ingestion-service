import asyncio

import pytest
import pytest_asyncio

from app.utils import singleton_registry


class TestSingletonRegistry:
    @pytest_asyncio.fixture(autouse=True)
    async def _clear_registry(self):
        await singleton_registry.close_all()
        yield
        await singleton_registry.close_all()

    def test_normalize_string(self):
        assert singleton_registry._normalize_key("AbC") == ("str", "abc")

    def test_normalize_type_and_instance(self):
        class A:
            pass

        _type = singleton_registry._normalize_key(A)
        _instance = singleton_registry._normalize_key(A())
        assert _type == _instance

    def test_normalize_generic(self):
        _generic = singleton_registry._normalize_key(list[int])
        assert _generic[0] == "generic"
        assert isinstance(_generic[1], tuple)

    @pytest.mark.asyncio
    async def test_create_and_get_sync_factory(self):
        class C:
            def __init__(self, value):
                self.value = value

        obj = await singleton_registry.create(
            C, factory=lambda value=1: C(value), value=5
        )
        assert isinstance(obj, C)
        assert obj.value == 5
        assert singleton_registry.get(C) is obj

    @pytest.mark.asyncio
    async def test_create_from_callable_key(self):
        class Counter:
            def __init__(self):
                self.count = 0

        obj = await singleton_registry.create(Counter)
        assert isinstance(obj, Counter)

    @pytest.mark.asyncio
    async def test_create_async_factory(self):
        async def factory():
            await asyncio.sleep(0)
            return {"ok": True}

        obj = await singleton_registry.create("key", factory=factory)
        assert obj == {"ok": True}

    @pytest.mark.asyncio
    async def test_concurrent_create_single_factory_called_once(self):
        calls: int = 0

        async def factory():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.01)
            return object()

        results = await asyncio.gather(
            *(singleton_registry.create("key", factory=factory) for _ in range(10))
        )
        assert all(result is results[0] for result in results)
        assert calls == 1

    @pytest.mark.asyncio
    async def test_factory_exception_does_not_leave_instance(self):
        async def bad():
            await asyncio.sleep(0)
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await singleton_registry.create("bad", factory=bad)

        with pytest.raises(KeyError):
            singleton_registry.get("bad")

    @pytest.mark.asyncio
    async def test_create_not_callable_key_no_factory(self):
        with pytest.raises(TypeError):
            await singleton_registry.create("some_key")

    @pytest.mark.asyncio
    async def test_create_key_already_exists(self):
        class A:
            pass

        class B:
            pass

        obj1 = await singleton_registry.create("some_key", factory=A)
        obj2 = await singleton_registry.create("some_key", factory=B)
        assert obj1 is obj2

    @pytest.mark.asyncio
    async def test_run_in_thread_flag(self):
        def sync_factory_check():
            try:
                asyncio.get_running_loop()
                return True
            except RuntimeError:
                return False

        v1 = await singleton_registry.create(
            "run_true", factory=sync_factory_check, run_in_thread=True
        )
        v2 = await singleton_registry.create(
            "run_false", factory=sync_factory_check, run_in_thread=False
        )
        assert v1 is False
        assert v2 is True

    @pytest.mark.asyncio
    async def test_close_all_calls_aclose_close_disconnect(self):
        events = []

        class AsyncClose:
            async def aclose(self):
                events.append("async")

        class SyncAClose:
            def aclose(self):
                events.append("sync_aclose")

        class Close:
            def close(self):
                events.append("close")

        class Disconnect:
            def disconnect(self):
                events.append("disconnect")

        singleton_registry._instances[("a",)] = AsyncClose()
        singleton_registry._instances[("b",)] = SyncAClose()
        singleton_registry._instances[("c",)] = Close()
        singleton_registry._instances[("d",)] = Disconnect()

        await singleton_registry.close_all()
        assert set(events) == {"async", "sync_aclose", "close", "disconnect"}

    @pytest.mark.asyncio
    async def test_get_raises_if_missing(self):
        with pytest.raises(KeyError):
            singleton_registry.get("some_key")

    @pytest.mark.asyncio
    async def test_generic_keys_different(self):
        obj1 = await singleton_registry.create(list[int], factory=lambda: object())
        obj2 = await singleton_registry.create(list[str], factory=lambda: object())
        assert obj1 is not obj2
