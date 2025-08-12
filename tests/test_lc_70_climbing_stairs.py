import setup_path

from lc_70_climbing_stairs  import ClimbingStairs

def test_solve():
    input = 2
    output = 2
    solution = ClimbingStairs()
    assert solution.solve(input) == output