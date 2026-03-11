import time


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 3, cooldown_s: int = 30):
        self.fail_threshold = fail_threshold
        self.cooldown_s = cooldown_s
        self.failures = {}  # model -> count
        self.open_until = {}  # model -> timestamp

    def allow(self, model: str) -> bool:
        until = self.open_until.get(model)
        return not until or time.time() >= until

    def record_success(self, model: str):
        self.failures[model] = 0
        self.open_until.pop(model, None)

    def record_failure(self, model: str):
        self.failures[model] = self.failures.get(model, 0) + 1
        if self.failures[model] >= self.fail_threshold:
            self.open_until[model] = time.time() + self.cooldown_s
