import json
import subprocess
import time

IMAGE = "faas-compare-factorial-py:0.1"

def run_once(n: int):
    cmd = ["docker", "run", "--rm", IMAGE, str(n)]

    t0 = time.perf_counter_ns()
    p = subprocess.run(cmd, capture_output=True, text=True)
    total_ns = time.perf_counter_ns() - t0

    if p.returncode != 0:
        raise RuntimeError(f"container failed rc={p.returncode} stderr={p.stderr.strip()}")

    payload = json.loads(p.stdout.strip())
    exec_ns = int(payload["exec_ns"])

    return {
        "total_container_ns": total_ns,
        "exec_ns_reported_by_container": exec_ns,
        "startup_container_ns": total_ns - exec_ns,
        "result": payload["result"],
    }

if __name__ == "__main__":
    print(run_once(34))