"""
MedianContainer skeleton for mock assessment.
Fill in the TODOs. You may change the internal data structure but keep the API.
"""
from typing import List

class MedianContainer:
    def __init__(self) -> None:
        # You may replace this with two heaps; a simple sorted list is acceptable.
        self._a: List[int] = []

    def add(self, x: int) -> None:
        """Insert one x into the container."""
        # TODO: implement (you may use bisect.insort)
        raise NotImplementedError

    def remove(self, x: int) -> bool:
        """
        Remove one occurrence of x if present and return True; else False.
        """
        # TODO: implement
        raise NotImplementedError

    def median(self) -> int:
        """
        Return the lower median.
        - For odd length n: element at index n//2
        - For even length n: element at index n//2 - 1
        Raise ValueError("empty") if container is empty.
        """
        # TODO: implement
        raise NotImplementedError
