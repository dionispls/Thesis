import json
import time
import tempfile
from pathlib import Path

import wasmtime


ROOT = Path(__file__).resolve().parents[1]
WASM_PATH = ROOT / "artifacts" / "wasm" / "factorial.wasm"


def run_once(n: int):
    engine = wasmtime.Engine()

    # 1) Готовим linker с WASI-импортами
    linker = wasmtime.Linker(engine)
    linker.define_wasi()  # <-- актуальный способ подключить WASI

    # 2) Готовим временный файл под stdout WASI-программы
    tmp = tempfile.NamedTemporaryFile(prefix="wasi_out_", suffix=".txt", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    # 3) startup = compile+instantiate (то, что делает окружение "готовым к вызову")
    t0 = time.perf_counter_ns()

    module = wasmtime.Module.from_file(engine, str(WASM_PATH))

    store = wasmtime.Store(engine)
    wasi = wasmtime.WasiConfig()
    wasi.argv = ["factorial_wasi", str(n)]
    wasi.stdout_file = str(tmp_path)  # stdout -> файл
    store.set_wasi(wasi)

    instance = linker.instantiate(store, module)

    startup_ns = time.perf_counter_ns() - t0

    # 4) exec = запуск _start (сама программа)
    t1 = time.perf_counter_ns()
    try:
        start = instance.exports(store)["_start"]
        start(store)
    except wasmtime.ExitTrap as e:
        # WASI-программы часто завершаются через proc_exit(0) -> ExitTrap(0)
        if getattr(e, "code", 0) != 0:
            raise
    total_exec_ns = time.perf_counter_ns() - t1

    out = tmp_path.read_text(encoding="utf-8").strip()
    tmp_path.unlink(missing_ok=True)

    payload = json.loads(out)

    return {
        "startup_wasm_ns": startup_ns,
        "total_exec_wasm_ns": total_exec_ns,          # wall time вызова _start
        "exec_ns_reported_by_wasm": payload["exec_ns"],  # время factorial внутри wasm
        "result": payload["result"],
    }


if __name__ == "__main__":
    print(run_once(34))