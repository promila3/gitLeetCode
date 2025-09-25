import random
import pytest

from src.median_container import MedianContainer

def build_sorted_copy(values):
    return sorted(values)

def lower_median(sorted_values):
    n = len(sorted_values)
    if n == 0:
        raise ValueError("empty")
    if n % 2 == 1:
        return sorted_values[n // 2]
    return sorted_values[n // 2 - 1]

def test_basic_sequence():
    mc = MedianContainer()
    with pytest.raises(ValueError):
        mc.median()

    for v in [1, 2, 5, 4]:
        mc.add(v)
    assert mc.median() == 2

    assert mc.remove(1) is True
    assert mc.median() == 4

def test_duplicates_and_empty():
    mc = MedianContainer()
    for v in [5, 3, 5]:
        mc.add(v)
    assert mc.median() == 5

    assert mc.remove(5) is True
    assert mc.remove(5) is True
    assert mc.remove(5) is False
    assert mc.median() == 3

    assert mc.remove(2) is False
    assert mc.remove(3) is True
    with pytest.raises(ValueError):
        mc.median()

    for v in [1,1,2,2,2]:
        mc.add(v)
    assert mc.median() == 2
    assert mc.remove(2) is True
    assert mc.median() == 1
    assert mc.remove(1) is True
    assert mc.median() == 2

def test_desc_then_delete_range():
    mc = MedianContainer()
    assert mc.remove(4) is False
    with pytest.raises(ValueError):
        mc.median()
    for i in range(10, 0, -1):
        mc.add(i)
    assert mc.median() == 5
    for i in range(4, 7):
        assert mc.remove(i) is True
    assert mc.median() == 7

def test_randomized_against_model(seed=42):
    random.seed(seed)
    mc = MedianContainer()
    model = []
    for _ in range(500):
        op = random.choice(["add", "remove", "median"])
        if op == "add":
            x = random.randint(-5, 5)
            mc.add(x)
            model.append(x)
        elif op == "remove":
            x = random.randint(-5, 5)
            got = mc.remove(x)
            if x in model:
                model.remove(x)  # remove one occurrence
                assert got is True
            else:
                assert got is False
        else:
            if len(model) == 0:
                with pytest.raises(ValueError):
                    mc.median()
            else:
                expect = lower_median(sorted(model))
                assert mc.median() == expect
