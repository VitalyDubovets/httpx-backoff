import pytest
from httpx_backoff.backoff_options import Constant


class TestBackoffConstantOption:
    @pytest.mark.parametrize("interval", [1, 2, 3, 4, 5])
    def test_backoff_constant(self, interval):
        constant_gen = Constant(interval=interval)

        for i in range(9):
            assert interval == next(constant_gen)
