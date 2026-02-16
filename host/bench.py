import json
import math
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from statistics import median

BASE_URL = "http://127.0.0.1:8000/invoke/"
REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"

INPUTS = [0, 1, 2, 5, 10, 20, 34]
REPEATS = 30
WARMUP = 1  # discard first result per (backend, n)


@dataclass
class Sample:
    host_total_ns: int
    exec_ns: int
    startup_ns: int
    result: str


def p95(values):
    if not values:
        return None
    xs = sorted(values)
    k = math.ceil(0.95 * len(xs)) - 1
    return xs[max(0, min(k, len(xs) - 1))]


def http_invoke(backend: str, n: int) -> dict:
    qs = urllib.parse.urlencode({"backend": backend, "n": str(n)})
    url = f"{BASE_URL}?{qs}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def run_case(backend: str, n: int) -> list[Sample]:
    samples: list[Sample] = []

    for i in range(REPEATS + WARMUP):
        t0 = time.perf_counter_ns()
        payload = http_invoke(backend, n)
        host_total_ns = time.perf_counter_ns() - t0

        if backend == "wasm":
            startup_ns = int(payload["startup_wasm_ns"])
            exec_ns = int(payload["exec_ns"])
        else:
            startup_ns = int(payload["startup_container_ns"])
            exec_ns = int(payload["exec_ns"])

        s = Sample(
            host_total_ns=host_total_ns,
            exec_ns=exec_ns,
            startup_ns=startup_ns,
            result=str(payload["result"]),
        )

        # discard warmup
        if i >= WARMUP:
            samples.append(s)

    return samples


def summarize(samples: list[Sample]) -> dict:
    host_totals = [s.host_total_ns for s in samples]
    startups = [s.startup_ns for s in samples]
    execs = [s.exec_ns for s in samples]

    return {
        "count": len(samples),
        "host_total_ns": {"median": int(median(host_totals)), "p95": int(p95(host_totals))},
        "startup_ns": {"median": int(median(startups)), "p95": int(p95(startups))},
        "exec_ns": {"median": int(median(execs)), "p95": int(p95(execs))},
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    run_id = time.strftime("%Y%m%d-%H%M%S")
    out_path = RESULTS_DIR / f"bench-v1-{run_id}.json"

    report = {
        "spec": {
            "inputs": INPUTS,
            "repeats": REPEATS,
            "warmup_discarded": WARMUP,
            "base_url": BASE_URL,
        },
        "cases": [],
    }

    for backend in ["wasm", "container"]:
        for n in INPUTS:
            samples = run_case(backend, n)
            # sanity: all results must match within case
            results = {s.result for s in samples}
            if len(results) != 1:
                raise RuntimeError(f"non-deterministic result for {backend} n={n}: {results}")

            case = {
                "backend": backend,
                "n": n,
                "summary": summarize(samples),
                "raw": [
                    {
                        "host_total_ns": s.host_total_ns,
                        "startup_ns": s.startup_ns,
                        "exec_ns": s.exec_ns,
                        "result": s.result,
                    }
                    for s in samples
                ],
            }
            report["cases"].append(case)
            print(f"done: {backend} n={n}")

    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()