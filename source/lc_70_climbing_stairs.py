class ClimbingStairs():
    def __init__(self):
        pass

    def climb(self, i: int, n: int) -> int:
        if i > n:
            return 0
        if i == n:
            return 1
        return self.climb(i+1, n) + self.climb(i+2, n)
    
    def solve(self, n: int)->int:
        return self.climb(0, n)
        
    