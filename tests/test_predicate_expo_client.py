import pytest
from httpx import Response, codes
from httpx_backoff.backoff_options import Expo
from httpx_backoff.backoff_options.jitter import use_equal_jitter
from httpx_backoff.clients.on_predicate import PredicateClient


@pytest.mark.asyncio
class TestPredicateExpoClient:
    async def test_success_request_without_retries(self, async_client, server):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(),
        ) as client:
            response: Response = await client.get(url=server.url.copy_with(path="/ping"))

            assert response.status_code == codes.OK
            assert server.config.app.counter == 1

        assert client.is_closed()

    @pytest.mark.parametrize("attempts", [5, 6])
    async def test_success_request_with_retry(self, async_client, server, attempts):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(),
            attempts=attempts,
        ) as client:
            response = await client.get(url=server.url.copy_with(path="/sometimes_error"))

            assert response.status_code == codes.OK
            assert server.config.app.counter > 1

        assert client.is_closed()

    @pytest.mark.parametrize("attempts", [2, 3, 4])
    async def test_failed_request_by_attempts(self, async_client, server, attempts):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(),
            attempts=attempts,
        ) as client:
            response = await client.get(url=server.url.copy_with(path="/bad_request"))

            assert response.status_code == codes.BAD_REQUEST
            assert server.config.app.counter == attempts

        assert client.is_closed()

    @pytest.mark.parametrize(
        "attempts,max_value,timeout",
        [
            (10, 2, 2),
            (12, 4, 3),
        ],
    )
    async def test_failed_request_by_timeout(self, async_client, server, attempts, max_value, timeout):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(max_value=max_value),
            attempts=attempts,
            timeout=timeout,
        ) as client:
            response = await client.get(url=server.url.copy_with(path="/bad_request"))

            assert response.status_code == codes.BAD_REQUEST
            assert server.config.app.counter < attempts

        assert client.is_closed()

    async def test_success_request_without_retry_with_equal_jitter(self, async_client, server):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(),
            jitter=use_equal_jitter,
        ) as client:
            response: Response = await client.get(url=server.url.copy_with(path="/ping"))

            assert response.status_code == codes.OK
            assert server.config.app.counter == 1

        assert client.is_closed()

    @pytest.mark.parametrize("attempts", [5, 6])
    async def test_success_request_with_using_equal_jitter_with_retry(self, async_client, server, attempts):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(),
            attempts=attempts,
            jitter=use_equal_jitter,
        ) as client:
            response = await client.get(url=server.url.copy_with(path="/sometimes_error"))

            assert response.status_code == codes.OK
            assert server.config.app.counter > 1

        assert client.is_closed()

    @pytest.mark.parametrize("attempts", [2, 3, 4])
    async def test_failed_request_with_equal_jitter(self, async_client, server, attempts):
        async with PredicateClient(
            predicate=lambda res: res.status_code != codes.OK,
            client=async_client,
            backoff_option=Expo(),
            attempts=attempts,
            jitter=use_equal_jitter,
        ) as client:
            response = await client.get(url=server.url.copy_with(path="/bad_request"))

            assert response.status_code == codes.BAD_REQUEST
            assert server.config.app.counter == attempts

        assert client.is_closed()
