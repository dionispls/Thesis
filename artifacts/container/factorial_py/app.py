import json
import sys
import time

def factorial(n: int) -> int:
    res = 1
    for i in range(2, n + 1):
        res *= i
    return res

def main():
    n = int(sys.argv[1])

    t0 = time.perf_counter_ns()
    result = factorial(n)
    exec_ns = time.perf_counter_ns() - t0

    print(json.dumps({
        "backend": "container",
        "n": n,
        "result": str(result),
        "exec_ns": exec_ns
    }))

if __name__ == "__main__":
    main()