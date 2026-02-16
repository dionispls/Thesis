import json
import subprocess
import tempfile
import time
from pathlib import Path

import wasmtime

REPO_ROOT = Path(__file__).resolve().parents[2]
WASM_PATH = REPO_ROOT / "artifacts" / "wasm" / "factorial.wasm"
CONTAINER_IMAGE = "faas-compare-factorial-py:0.1"

def invoke_wasm_cold(n: int) -> dict:
    engine = wasmtime.Engine()
    linker = wasmtime.Linker(engine)
    linker.define_wasi()

    tmp = tempfile.NamedTemporaryFile(prefix="wasi_out_", suffix=".txt", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    t0 = time.perf_counter_ns()

    module = wasmtime.Module.from_file(engine, str(WASM_PATH))
    store = wasmtime.Store(engine)

    wasi = wasmtime.WasiConfig()
    wasi.argv = ["factorial_wasi", str(n)]
    wasi.stdout_file = str(tmp_path)
    store.set_wasi(wasi)

    instance = linker.instantiate(store, module)

    startup_wasm_ns = time.perf_counter_ns() - t0

    t1 = time.perf_counter_ns()
    try:
        start = instance.exports(store)["_start"]
        start(store)
    except wasmtime.ExitTrap as e:
        if getattr(e, "code", 0) != 0:
            raise
    total_exec_wasm_ns = time.perf_counter_ns() - t1

    out = tmp_path.read_text(encoding="utf-8").strip()
    tmp_path.unlink(missing_ok=True)

    payload = json.loads(out)
    return {
        "backend": "wasm",
        "n": n,
        "result": payload["result"],
        "startup_wasm_ns": startup_wasm_ns,
        "total_exec_wasm_ns": total_exec_wasm_ns,
        "exec_ns": int(payload["exec_ns"]),  # pure factorial inside wasm
    }


def invoke_container_cold(n: int) -> dict:

    cmd = ["docker", "run", "--rm", CONTAINER_IMAGE, str(n)]

    t0 = time.perf_counter_ns()
    p = subprocess.run(cmd, capture_output=True, text=True)
    total_container_ns = time.perf_counter_ns() - t0

    if p.returncode != 0:
        raise RuntimeError(f"container failed rc={p.returncode} stderr={p.stderr.strip()}")

    payload = json.loads(p.stdout.strip())
    exec_ns = int(payload["exec_ns"])

    return {
        "backend": "container",
        "n": n,
        "result": payload["result"],
        "total_container_ns": total_container_ns,
        "startup_container_ns": total_container_ns - exec_ns,
        "exec_ns": exec_ns,  # pure factorial inside container
    }