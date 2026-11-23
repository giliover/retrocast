"""Reusable bounded pagination for any sequence-backed UI list."""
from dataclasses import dataclass
from math import ceil

@dataclass
class Paginator:
    page: int = 0
    page_size: int = 5

    def pages(self, count: int) -> int:
        return max(1, ceil(count / max(1, self.page_size)))

    def clamp(self, count: int) -> None:
        self.page = max(0, min(self.page, self.pages(count) - 1))

    def view(self, items):
        self.clamp(len(items))
        size = max(1, self.page_size)
        return items[self.page * size:(self.page + 1) * size]

    def move(self, delta: int, count: int) -> None:
        self.page += delta
        self.clamp(count)

    def reset(self) -> None:
        self.page = 0

    def label(self, count: int) -> str:
        self.clamp(count)
        return f"{self.page + 1}/{self.pages(count)}"
