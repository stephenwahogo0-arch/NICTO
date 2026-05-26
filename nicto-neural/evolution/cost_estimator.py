"""Cost estimator — training time and resource prediction."""

import time


class CostEstimator:
    """Estimates training cost, time, and compute resources."""

    FLOPS_PER_PARAM = 6

    def __init__(self, config):
        self.config = config
        self._benchmarks: list[dict] = []

    def estimate_training_cost(
        self,
        dataset_size: int,
        epochs: int = 10,
        batch_size: int = None,
    ) -> dict:
        batch = batch_size or self.config.batch_size
        batches_per_epoch = max(1, dataset_size // batch)
        total_batches = batches_per_epoch * epochs

        params = self._estimate_params()
        flops = params * self.FLOPS_PER_PARAM * total_batches * batch

        seconds_estimate = flops / 1e12

        return {
            "dataset_size": dataset_size,
            "epochs": epochs,
            "batch_size": batch,
            "total_batches": total_batches,
            "estimated_params": params,
            "estimated_flops": flops,
            "estimated_seconds": seconds_estimate,
            "estimated_minutes": seconds_estimate / 60,
        }

    def _estimate_params(self) -> int:
        d = self.config.d_model
        ff = self.config.d_ff
        layers = self.config.n_layers
        vocab = self.config.vocab_size
        n_experts = self.config.n_experts

        embedding_params = vocab * d
        attention_params = 4 * d * d * layers
        ffn_params = 2 * d * ff * layers * n_experts
        head_params = 6 * d * vocab

        return embedding_params + attention_params + ffn_params + head_params

    def benchmark(self, func, n_iterations: int = 5) -> dict:
        """Benchmark a function's execution time."""
        times = []
        for _ in range(n_iterations):
            start = time.time()
            func()
            elapsed = time.time() - start
            times.append(elapsed)

        avg = sum(times) / len(times)
        result = {
            "iterations": n_iterations,
            "avg_seconds": avg,
            "min_seconds": min(times),
            "max_seconds": max(times),
        }
        self._benchmarks.append(result)
        return result

    def get_benchmarks(self) -> list[dict]:
        return self._benchmarks
