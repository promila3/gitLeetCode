"""
Reference solution (two-heaps + lazy deletion).
Time:
- add/remove/median: O(log n) amortized
Behavior:
- "Lower median" invariant: left heap (max-heap) always holds the median.
"""
import heapq
from collections import defaultdict

class MedianContainer:
    def __init__(self) -> None:
        # left: max-heap via negatives; right: min-heap
        self.left = []   # stores negatives
        self.right = []  # stores positives
        self.left_size = 0   # counts of valid elements in left
        self.right_size = 0  # counts of valid elements in right
        self.delayed = defaultdict(int)  # values scheduled for deletion
        self.freq = defaultdict(int)     # actual multiset counts
        self.n = 0

    # Helpers
    def _prune_left(self):
        while self.left and self.delayed[-self.left[0]] > 0:
            v = -heapq.heappop(self.left)
            self.delayed[v] -= 1

    def _prune_right(self):
        while self.right and self.delayed[self.right[0]] > 0:
            v = heapq.heappop(self.right)
            self.delayed[v] -= 1

    def _rebalance(self):
        # ensure left_size >= right_size and difference <= 1
        if self.left_size < self.right_size:
            # move one from right to left
            self._prune_right()
            v = heapq.heappop(self.right)
            heapq.heappush(self.left, -v)
            self.right_size -= 1
            self.left_size += 1
            self._prune_right()
        elif self.left_size - self.right_size > 1:
            # move one from left to right
            self._prune_left()
            v = -heapq.heappop(self.left)
            heapq.heappush(self.right, v)
            self.left_size -= 1
            self.right_size += 1
            self._prune_left()

    def add(self, x: int) -> None:
        if self.left_size == 0:
            heapq.heappush(self.left, -x)
            self.left_size += 1
        else:
            self._prune_left()
            median = -self.left[0] if self.left else (self.right[0] if self.right else x)
            if x <= median:
                heapq.heappush(self.left, -x)
                self.left_size += 1
            else:
                heapq.heappush(self.right, x)
                self.right_size += 1
        self.freq[x] += 1
        self.n += 1
        self._rebalance()

    def remove(self, x: int) -> bool:
        if self.freq[x] == 0:
            return False
        self.freq[x] -= 1
        self.delayed[x] += 1
        self.n -= 1

        # Decide which heap's "size" to decrement based on current median
        self._prune_left()
        median = -self.left[0] if self.left else (self.right[0] if self.right else x)
        if x <= median:
            self.left_size -= 1
            if self.left_size < 0:
                self.left_size = 0  # safety
        else:
            self.right_size -= 1
            if self.right_size < 0:
                self.right_size = 0  # safety

        # Clean up tops if needed and rebalance
        self._prune_left()
        self._prune_right()
        self._rebalance()
        self._prune_left()
        return True

    def median(self) -> int:
        if self.n == 0:
            raise ValueError("empty")
        self._prune_left()
        return -self.left[0]
