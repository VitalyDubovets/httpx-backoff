import pytest
from httpx_backoff.backoff_options import Expo


class TestBackoffExpoOption:
    @pytest.mark.parametrize("range_number", [1, 3, 5, 7, 9, 11])
    def test_backoff_expo_with_defaults_args(self, range_number):
        expo_gen = Expo()

        for i in range(range_number):
            assert 2**i == expo_gen.send(None)

    @pytest.mark.parametrize(
        "base,factor,range_number",
        [
            (3, 2, 5),
            (4, 5, 20),
            (5, 9, 10),
            (1, 1, 1),
        ],
    )
    def test_backoff_expo_with_args(self, base, factor, range_number):
        expo_gen = Expo(base=base, factor=factor)

        for i in range(range_number):
            assert factor * base**i == expo_gen.send(None)

    @pytest.mark.parametrize("max_value, expected", [(16, [1, 2, 4, 8, 16, 16, 16]), (32, [1, 2, 4, 8, 16, 32, 32])])
    def test_expo_max_value(self, max_value, expected):
        expo_gen = Expo(max_value=max_value)

        for expect in expected:
            assert expect == next(expo_gen)
