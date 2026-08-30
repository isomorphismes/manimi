import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def _load_runtime_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_ithon_runtime() -> ModuleType:
    ithon_lib = Path(os.environ.get("ITHON_LIB", ROOT.parent / "ithon" / "Lib"))
    _load_runtime_module("ithon_static", ithon_lib / "ithon_static.py")
    _load_runtime_module("ithon_frontend", ithon_lib / "ithon_frontend.py")
    return _load_runtime_module("ithon_run", ithon_lib / "ithon_run.py")


def load_checked_ithon(path: Path, module_name: str) -> ModuleType:
    runtime = load_ithon_runtime()
    loader = runtime.IthonSourceLoader(module_name, str(path))
    spec = importlib.util.spec_from_file_location(module_name, path, loader=loader)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create an Ithon loader for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module
