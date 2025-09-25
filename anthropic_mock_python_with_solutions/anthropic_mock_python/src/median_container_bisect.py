"""
Reference solution (bisect-based): simpler, correctness-first.
Time:
- add/remove: O(n) due to list shifts
- median: O(1)
"""
from typing import List
import bisect

class MedianContainer:
    def __init__(self) -> None:
        self._a: List[int] = []

    def add(self, x: int) -> None:
        bisect.insort(self._a, x)

    def remove(self, x: int) -> bool:
        i = bisect.bisect_left(self._a, x)
        if i == len(self._a) or self._a[i] != x:
            return False
        self._a.pop(i)
        return True

    def median(self) -> int:
        if not self._a:
            raise ValueError("empty")
        n = len(self._a)
        idx = n // 2 if n % 2 == 1 else n // 2 - 1
        return self._a[idx]
