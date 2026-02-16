# Metrics v1

## Function contract
Input: N in [0,34]
Output: N! (decimal string)

## Artifact size
- wasm_bytes: size of factorial.wasm in bytes
- oci_bytes: docker image .Size in bytes (docker image inspect)

## Timing
All times are measured by host (Python) in nanoseconds using perf_counter_ns.

### WASM
- startup_wasm_ns: time to make module ready to call (load/compile/instantiate)
- exec_wasm_ns: time of a single factorial call after instantiation

### OCI
- total_container_ns: wall time of `docker run --rm image N`
- exec_container_ns: time printed by program inside container for factorial computation
- startup_container_ns = total_container_ns - exec_container_ns

## Experiment protocol
- repeats: 30 (later can increase)
- report: median + p95 (later can add CI)
- warmup: discard first run per backend
- input set: [0, 1, 2, 5, 10, 20, 34]