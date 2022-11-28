from httpx_backoff.backoff_options import Runtime


class TestBackoffRuntimeOption:
    def test_backoff_runtime(self):
        runtime_gen = Runtime(func=lambda x: x)

        for i in range(20):
            assert i == runtime_gen.send(i)
