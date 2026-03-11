# app/services/circuit_breaker.py

import time


class CircuitBreaker:
    """
    Simple in-memory circuit breaker per model.

    After `fail_threshold` consecutive failures the circuit opens
    and all requests are rejected for `cooldown_s` seconds.
    """

    def __init__(self, fail_threshold: int = 3, cooldown_s: int = 30):
        self.fail_threshold = fail_threshold
        self.cooldown_s = cooldown_s
        self.failures: dict = {}  # model -> failure count
        self.open_until: dict = {}  # model -> re-open timestamp

    def allow(self, model: str) -> bool:
        """Return True if the circuit is closed (requests allowed)."""
        until = self.open_until.get(model)
        return not until or time.time() >= until

    def record_success(self, model: str) -> None:
        self.failures[model] = 0
        self.open_until.pop(model, None)

    def record_failure(self, model: str) -> None:
        self.failures[model] = self.failures.get(model, 0) + 1
        if self.failures[model] >= self.fail_threshold:
            self.open_until[model] = time.time() + self.cooldown_s
