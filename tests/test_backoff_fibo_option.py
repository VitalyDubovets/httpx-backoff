import pytest
from httpx_backoff.backoff_options import Fibo


class TestBackoffFiboOption:
    @pytest.mark.parametrize(
        "expected",
        [[1, 1, 2, 3, 5, 8, 13], [1, 1, 2, 3, 5, 8, 13, 21, 34]],
    )
    def test_backoff_fibo_with_default_args(self, expected):
        fibo_gen = Fibo()

        for expect in expected:
            assert expect == next(fibo_gen)

    @pytest.mark.parametrize(
        "max_value,expected",
        [(8, [1, 1, 2, 3, 5, 8, 8, 8]), (9, [1, 1, 2, 3, 5, 8, 9]), (16, [1, 1, 2, 3, 5, 8, 13, 16])],
    )
    def test_backoff_fibo_with_max_value(self, max_value, expected):
        fibo_gen = Fibo(max_value=max_value)

        for expect in expected:
            assert expect == next(fibo_gen)
