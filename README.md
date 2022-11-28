httpx-backoff
=======

**Клиент для отправки повторных http запросов**

Этот пакет расширения httpx для асинхронных запросов предоставляет возможность повторно отправлять запросы на какой-либо сервис
при возникновениях каки-либо предвиденных ситуация в целях попытаться получить нужный ответ с
определенными таймаутами, 
если выбранный сервис временно недоступен

Установка
=====

Python >= 3.10

`pip install httpx-backoff`

`poetry add httpx-backoff`

`pipenv install httpx-backoff`

Документация 
=====

### ***PredicateClient***

Этот клиент, который позволяет вам делать повторные попытки запросов,
если условие в виде функции не соответствует результату

```python
class PredicateClient(CustomClient):
    """
    Client bases on a retry way on predicate
    """
    def __init__(
        self,
        predicate: Callable[[Response], bool],
        *,
        client: AsyncClient,
        backoff_option_gen: Generator[int, None, None],
        attempts: int = 5,
        timeout: Optional[float] = None,
        jitter: Optional[Callable[[float], float]] = use_full_jitter,
    ): ...
```
`predicate` - аргумент принимает в себя функцию или класс, которые на основе Response принимают
решение о повторном запросе к ресурсу. 

*Пример:*
```python
PredicateClient(
    predicate=lambda res: res.status_code != codes.OK,
    client=async_client,
    backoff_option_gen=Expo(),
)
```

`client` - асинхронный клиент от библиотеки httpx

`backoff_option_gen` - генератор, для высчитывания повторной попытки отправки запроса

`attempts` - количество повторных запросов

`timeout` - максимальное время выполнения повторных запросов со стороны клиента

`jitter` - функция, реализующая алгоритм jitter, который позволяет добавить некоторую случайность в алгоритм отсрочки,
чтобы распределить повторы операций во времени. Например: `use_full_jitter` или `use_equal_jitter`.

Подробнее
[тут](https://aws.amazon.com/ru/builders-library/timeouts-retries-and-backoff-with-jitter/) и 
[тут](https://aws.amazon.com/ru/blogs/architecture/exponential-backoff-and-jitter/)

### ***ExceptionClient***

Этот клиент, который позволяет вам делать повторные попытки запросов,
если условие в виде функции не соответствует результату

```python
class ExceptionClient(CustomClient):
    """
    Client bases on a retry way on exception
    """

    def __init__(
        self,
        exception: _ExceptionGroup,
        *,
        client: AsyncClient,
        backoff_option_gen: Generator[int, None, None],
        attempts: int = 5,
        timeout: Optional[float] = None,
        jitter: Optional[Callable[[float], float]] = use_full_jitter,
    ): ...
```
`exception` - аргумент принимает в себя исключение или группу исключений в виде ```tuple[BaseException, ...]```
при перехватки которых, клиент будет пытаться повторить запрос к сервису

*Пример:*
```python
ExceptionClient(
    exception=(ReadTimeout,),
    client=async_client,
    backoff_option_gen=Constant(),
)
```

`client` - асинхронный клиент от библиотеки httpx

`backoff_option_gen` - генератор, для высчитывания повторной попытки отправки запроса

`attempts` - количество повторных запросов

`timeout` - максимальное время выполнения повторных запросов со стороны клиента

`jitter` - функция, реализующая алгоритм jitter, который позволяет добавить некоторую случайность в алгоритм отсрочки,
чтобы распределить повторы операций во времени. Например: `use_full_jitter` или `use_equal_jitter`.

Подробнее
[тут](https://aws.amazon.com/ru/builders-library/timeouts-retries-and-backoff-with-jitter/) и 
[тут](https://aws.amazon.com/ru/blogs/architecture/exponential-backoff-and-jitter/)


### ***Backoff options***

Для каждого экземпляра классов `PredicateClient` и `ExceptionClient` должны указываться backoff настройки
в его конструкторе

*Пример:*

```python
PredicateClient(
    predicate=lambda res: res.status_code != codes.OK,
    client=async_client,
    backoff_option=Expo(),
)
```

Backoff настройки позволяют вам определить время, через которое будет отправлен повторный запрос на обращающийся сервис

В данные момент доступны несколько backoff настроек: 
- ```Expo``` - настройка гарантирует рост времени по экспоненте
```python
class Expo(Generator):
    """
    Generator for exponential decay.
    """

    def __init__(self, *, max_value: Optional[int] = None, base: int = 2, factor: int = 1):
        """
        :param base: The mathematical base of the exponentiation operation
        :param factor: Factor to multiply the exponentiation by.
        :param max_value: The maximum value to yield. Once the value in the
        true exponential sequence exceeds this, the value
        of max_value will forever after be yielded.
        """
        self._base = base
        self._factor = factor
        self._max_value = max_value
        self._attempt = 0
        self._value: int = 0
```
- ```Fibo``` - настройка гарантирует рост времени по последовательности чисел Фиббоначи с возможностью указать
максимальное число, которое играет роль ограничения последовательности и будет отдавать при достижении её ограничения
```python
class Fibo(Generator):
    """
    Generator for fibonaccial decay.
    """

    def __init__(self, max_value: Optional[int] = None):
        """
        :param max_value: The maximum value to yield. Once the value in the
         true fibonacci sequence exceeds this, the value
         of max_value will forever after be yielded.
        """
        self._max_value = max_value
        self._a = 1
        self._b = 1
```
- ```Constant``` - настройка гарантирует повторные запросы к сервисы за константное время
```python
class Constant(Generator):
    """
    Generator for constant intervals.
    """

    def __init__(self, interval: int = 1):
        """
        :param interval: A constant interval to yield or an iterable of such values.
        """
        self._interval = itertools.repeat(interval)
```
- ```Runtime``` - настройка позволяет вам указать функцию, которая будет высчитывать время на основе
вашей кастомной логике
```python
class Runtime(Generator):
    """
    Generator that is based on parsing the return func or thrown
    exception to the decorated method
    """

    def __init__(self, func: Callable[[Any], int]):
        self._func = func
```
### ***Jitter***

Jitter алгоритм может быть указан в конструкторе классов `PredicateClient` и `ExceptionClient`. По умолчанию используется
*full jitter*, так как является более предпочтительным и эффективным, однако вы можете использовать *equal jitter*
или же вовсе отказаться от него передав в аргумент
конструктора ```None```

**Примеры использования:**

- Передача алгоритма `full jitter` в конструктор класса
```python
from httpx import AsyncClient, codes

from httpx_backoff.backoff_options import Expo
from httpx_backoff.backoff_options.jitter import use_full_jitter
from httpx_backoff.clients.on_predicate import PredicateClient

PredicateClient(
    predicate=lambda res: res.status_code != codes.OK,
    client=AsyncClient(),
    backoff_option=Expo(),
    jitter=use_full_jitter,
)
```

- Передача алгоритма `equal jitter` в конструктор класса
```python
from httpx import AsyncClient, codes

from httpx_backoff.backoff_options import Expo
from httpx_backoff.backoff_options.jitter import use_equal_jitter
from httpx_backoff.clients.on_predicate import PredicateClient

PredicateClient(
    predicate=lambda res: res.status_code != codes.OK,
    client=AsyncClient(),
    backoff_option=Expo(),
    jitter=use_equal_jitter,
)
```

- Передача `None` в аргумент конструктора для отмены использования алгоритма
```python
from httpx import AsyncClient, codes

from httpx_backoff.backoff_options import Expo
from httpx_backoff.clients.on_predicate import PredicateClient

PredicateClient(
    predicate=lambda res: res.status_code != codes.OK,
    client=AsyncClient(),
    backoff_option=Expo(),
    jitter=None,
)
```