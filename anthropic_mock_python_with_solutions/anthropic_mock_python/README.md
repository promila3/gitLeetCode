# Anthropic-Style Mock: Progressive Filesystem (Python)

**Format:** Multiple files + unit tests (pytest).  
**Task:** Implement a median-enabled multiset-like container that supports duplicates and deletions.

## Problem
Implement `MedianContainer` with methods:
- `add(x: int) -> None`
- `remove(x: int) -> bool` — removes one occurrence of `x` if present and returns True; else False.
- `median() -> int` — returns the **lower median** (for even n, element at index n//2 - 1 in 0-based order).  
  Raise `ValueError("empty")` if the container is empty.

### Constraints & Notes
- Multiple duplicates allowed.
- Aim for **O(log n)** per operation using two heaps *or* a `bisect`-based list (simpler, O(n) inserts) — correctness first.
- Keep the class small and clean; tests favor correctness and robust edge handling.

## Layout
```
anthropic_mock_python/
  src/median_container.py       # ← fill in TODOs
  tests/test_median_container.py
```

## Run
```bash
pip install -q pytest
pytest -q
```


## Reference Implementations
- `src/median_container_bisect.py` (simpler)
- `src/median_container_heaps.py` (O(log n) ops)
