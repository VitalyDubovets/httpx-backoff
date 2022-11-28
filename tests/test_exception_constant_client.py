import pytest
from httpx import ReadTimeout, Response, codes
from httpx_backoff.backoff_options import Constant
from httpx_backoff.backoff_options.jitter import use_equal_jitter
from httpx_backoff.clients.on_exception import ExceptionClient


@pytest.mark.asyncio
class TestOnExceptionConstantClient:
    async def test_success_request_without_retries(self, async_client, server):
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(),
        ) as client:
            response: Response = await client.get(url=server.url.copy_with(path="/ping"))

            assert response.status_code == codes.OK
            assert server.config.app.counter == 1

        assert client.is_closed()

    async def test_success_request_with_retries(self, async_client, server):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(),
        ) as client:
            response: Response = await client.get(url=server.url.copy_with(path="/sometimes_slow_response"))

            assert response.status_code == codes.OK
            assert server.config.app.counter > 1

        assert client.is_closed()

    @pytest.mark.parametrize("attempts", [2, 3, 4, 5, 6])
    async def test_failed_request_by_attempts(self, async_client, server, attempts):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(),
            attempts=attempts,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()

    @pytest.mark.parametrize(
        "interval,timeout",
        [
            (1, 2),
            (2, 3),
        ],
    )
    async def test_failed_request_by_timeout(self, async_client, server, interval, timeout):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(interval=interval),
            timeout=timeout,
            attempts=5,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()

    async def test_success_request_without_retries_using_equal_jitter(self, async_client, server):
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(),
            jitter=use_equal_jitter,
        ) as client:
            response: Response = await client.get(url=server.url.copy_with(path="/ping"))

            assert response.status_code == codes.OK
            assert server.config.app.counter == 1

        assert client.is_closed()

    async def test_success_request_with_retries_using_equal_jitter(self, async_client, server):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(),
            jitter=use_equal_jitter,
        ) as client:
            response: Response = await client.get(url=server.url.copy_with(path="/sometimes_slow_response"))

            assert response.status_code == codes.OK
            assert server.config.app.counter > 1

        assert client.is_closed()

    @pytest.mark.parametrize("attempts", [2, 3, 4, 5, 6])
    async def test_failed_request_by_attempts_using_equal_jitter(self, async_client, server, attempts):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(),
            attempts=attempts,
            jitter=use_equal_jitter,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()

    @pytest.mark.parametrize(
        "interval,timeout",
        [
            (1, 2),
            (2, 3),
        ],
    )
    async def test_failed_request_by_timeout_using_equal_jitter(self, async_client, server, interval, timeout):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Constant(interval=interval),
            timeout=timeout,
            attempts=5,
            jitter=use_equal_jitter,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()
