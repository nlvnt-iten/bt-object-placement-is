class IDGenerator:
    def __init__(self):
        self._current = 1

    def set_min(self, min_id: int) -> None:
        if min_id < 1:
            raise ValueError("Minimum ID must be greater than 0.")
        if min_id > self._current:
            self._current = min_id

    def generate(self) -> int:
        next_id = self._current
        self._current += 1
        return next_id
