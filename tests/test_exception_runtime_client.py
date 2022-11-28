import pytest
from httpx import ReadTimeout, Response, codes
from httpx_backoff.backoff_options import Runtime
from httpx_backoff.backoff_options.jitter import use_equal_jitter
from httpx_backoff.clients.on_exception import ExceptionClient


@pytest.mark.asyncio
class TestOnExceptionRuntimeClient:
    async def test_success_request_without_retries(self, async_client, server):
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Runtime(func=lambda x: 1 + 1),
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
            backoff_option=Runtime(func=lambda x: 1 + 1),
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
            backoff_option=Runtime(func=lambda x: 1 + 1),
            attempts=attempts,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()

    @pytest.mark.parametrize("timeout", [2, 3])
    async def test_failed_request_by_timeout(self, async_client, server, timeout):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Runtime(func=lambda x: 1 + 1),
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
            backoff_option=Runtime(func=lambda x: 1 + 1),
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
            backoff_option=Runtime(func=lambda x: 1 + 1),
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
            backoff_option=Runtime(func=lambda x: 1 + 1),
            attempts=attempts,
            jitter=use_equal_jitter,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()

    @pytest.mark.parametrize("timeout", [2, 3])
    async def test_failed_request_by_timeout_using_equal_jitter(self, async_client, server, timeout):
        async_client.timeout = 0.2
        async with ExceptionClient(
            exception=(ReadTimeout,),
            client=async_client,
            backoff_option=Runtime(func=lambda x: 1 + 1),
            timeout=timeout,
            attempts=5,
            jitter=use_equal_jitter,
        ) as client:
            with pytest.raises(ReadTimeout):
                await client.get(url=server.url.copy_with(path="/slow_response"))

        assert client.is_closed()
