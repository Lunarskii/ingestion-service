import asyncio
import inspect
from functools import partial
from typing import (
    Any,
    Callable,
    Hashable,
    get_args,
    get_origin,
)


Key = str | type | Any
NormalizedKey = Hashable


class SingletonRegistry:
    """
    Асинхронно-безопасный реестр с нормализацией ключей.

    Нормализация ключа:
      - str -> ("str", key_lower)
      - class/type -> ("type", module, qualname)
      - instance -> ("type", instance.__class__.__module__, instance.__class__.__qualname__)
      - typing generics -> ("generic", normalized_origin, (normalized_args...))
      - прочее -> ("obj", repr(obj))

    Реестр поддерживает создание объектов с помощью фабрик, которые могут быть как обычными
    вызываемыми объектами, так и функциями. Создание защищено локами для каждого ключа и
    глобальным локом для инициализации локов для каждого ключа. Одновременные запросы на создание одного
    и того же ключа будет ждать выполнения первой задачи создания и вернет тот же экземпляр.
    """

    def __init__(self):
        self._instances: dict[NormalizedKey, Any] = {}
        self._locks: dict[NormalizedKey, asyncio.Lock] = {}
        self._creating: dict[NormalizedKey, asyncio.Task] = {}
        self._global_lock = asyncio.Lock()

    def _normalize_key(self, key: Key) -> NormalizedKey:
        """
        Приводит входной key к хэшируемой, детерминированной форме.
        Поддерживает строки, типы/экземпляры и typing generics.
        """

        if isinstance(key, str):
            return "str", key.lower()

        origin = get_origin(key)
        if origin is not None:
            normalized_origin = self._normalize_key(origin)
            args: tuple = get_args(key)
            normalized_args = tuple(self._normalize_key(a) for a in args)
            return "generic", normalized_origin, normalized_args

        if isinstance(key, type):
            return "type", key.__module__, key.__qualname__

        cls = getattr(key, "__class__", None)
        if isinstance(cls, type):
            return "type", cls.__module__, cls.__qualname__

        return "obj", repr(key)

    def get(self, key: Key) -> Any:
        """
        Получаем экземпляр singleton для ключа ``key``.

        :param key: Ключ, по которому хранится экземпляр.
        :type key: Key
        :return: Экземпляр.
        :raises KeyError: Если для нормализованного ключа не существует экземпляра.
        """

        k = self._normalize_key(key)
        if k not in self._instances:
            raise KeyError(f"Singleton for key {key!r} is not created")
        return self._instances[k]

    async def create(
        self,
        key: Key,
        factory: Callable[..., Any] | None = None,
        *args,
        run_in_thread: bool = True,
        **kwargs,
    ) -> Any:
        """
        Создает или возвращает экземпляр singleton, связанный с ключом ``key``.

        Если factory is None и ``key`` — callable (обычно класс), то используется ``key`` как фабрика.
        Примеры:
            - await registry.create(MyModel)                # вызывает MyModel()
            - await registry.create(MyModel, MyModel)       # то же самое
            - await registry.create("foo", factory_callable)
            - await registry.create(MyModel, run_in_thread=False)  # вызовет MyModel() в event loop

        :param key: Ключ, по которому будет храниться экземпляр.
        :type key: Key
        :param factory: Вызываемая функция или корутина, которая создает экземпляр.
        :type factory: Callable[..., Any] | None
        :param args: Аргументы для фабрики.
        :type args: Any
        :param run_in_thread: Если фабрика является обычным блокирующим вызовом и значение run_in_thread равно True, то
            фабрика будет запущена в отдельном потоке через asyncio.to_thread. Если значение False, то фабрика будет
            запущена в текущем потоке цикла обработки событий.
        :param kwargs: keyword-аргументы для фабрики.
        :type kwargs: Any
        """

        if factory is None:
            if callable(key):
                factory = key
            else:
                raise TypeError(
                    "Фабрика не указана и ключ (key) не может быть вызван. "
                    "Укажите фабрику или передайте вызываемый ключ (например, класс)."
                )

        key = self._normalize_key(key)

        if key in self._instances:
            return self._instances[key]

        async with self._global_lock:
            lock: asyncio.Lock | None = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock

        async with lock:
            if key in self._instances:
                return self._instances[key]

            task: asyncio.Task = self._creating.get(key)
            if task is not None:
                return await task

            loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
            task = loop.create_task(
                self._run_factory_and_store(
                    key=key,
                    factory=factory,
                    args=args,
                    kwargs=kwargs,
                    run_in_thread=run_in_thread,
                )
            )
            self._creating[key] = task

            try:
                result = await task
            finally:
                await self._creating.pop(key, None)

            return result

    async def _run_factory_and_store(
        self,
        key: NormalizedKey,
        factory: Callable[..., Any],
        args,
        kwargs,
        run_in_thread: bool,
    ) -> Any:
        """
        Запускает фабрику (синхронную или асинхронную) и сохраняет созданный экземпляр.

        Гарантирует, что в случае исключения частично созданный экземпляр не будет сохранен.
        """

        try:
            if inspect.iscoroutinefunction(factory):
                obj: Any = await factory(*args, **kwargs)
            else:
                if run_in_thread:
                    obj: Any = await asyncio.to_thread(
                        partial(factory, *args, **kwargs)
                    )
                else:
                    obj: Any = factory(*args, **kwargs)

            self._instances[key] = obj
            return obj
        except Exception:
            self._instances.pop(key, None)
            raise

    def _clear(self) -> None:
        """
        Очищает внутреннее состояние (экземпляры, локи, пул задач).

        Примечание: Не рекомендуется вызывать, используйте close_all().
        """

        self._instances.clear()
        self._creating.clear()
        self._locks.clear()

    async def close_all(self) -> None:
        """
        Закрывает и очищает все зарегистрированные экземпляры.
        """

        async def _close_one(obj: Any) -> None:
            if hasattr(obj, "aclose") and inspect.iscoroutinefunction(obj.aclose):
                try:
                    await obj.aclose()
                    return
                except Exception:
                    pass
            if hasattr(obj, "aclose"):
                try:
                    obj.aclose()
                    return
                except Exception:
                    pass
            if hasattr(obj, "close"):
                try:
                    obj.close()
                    return
                except Exception:
                    pass
            if hasattr(obj, "disconnect"):
                try:
                    obj.disconnect()
                    return
                except Exception:
                    pass

        tasks = [_close_one(obj) for obj in list(self._instances.values())]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._clear()


singleton_registry = SingletonRegistry()
