from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .runtime import invoke_container_cold, invoke_wasm_cold


@require_GET
def invoke(request):
    backend = request.GET.get("backend")
    n_raw = request.GET.get("n")

    if backend not in {"wasm", "container"}:
        return JsonResponse({"error": "backend must be wasm or container"}, status=400)

    try:
        n = int(n_raw)
    except (TypeError, ValueError):
        return JsonResponse({"error": "n must be integer"}, status=400)

    try:
        if backend == "wasm":
            payload = invoke_wasm_cold(n)
        else:
            payload = invoke_container_cold(n)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(payload)