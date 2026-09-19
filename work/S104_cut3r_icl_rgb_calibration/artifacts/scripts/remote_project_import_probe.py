import importlib, json, os, sys

mods = [
    "modeling",
    "modeling.pipeline",
    "modeling.modules.conditioner",
    "modeling.modules.autoencoder",
    "utils.util",
]
out = {
    "python": sys.version,
    "cwd": os.getcwd(),
    "data_access": False,
    "weight_access": False,
    "model_execution": False,
    "results": {},
}
for m in mods:
    try:
        importlib.import_module(m)
        out["results"][m] = "IMPORT_OK"
    except Exception as e:
        out["results"][m] = f"FAIL {type(e).__name__}: {e}"
print(json.dumps(out, ensure_ascii=False, indent=2))
