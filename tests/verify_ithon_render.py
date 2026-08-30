import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

from tests.elliptic_semantics import elliptic_semantic_receipt
from tests.ithon_support import load_checked_ithon


ROOT = Path(__file__).resolve().parents[1]
VIDEOS = ROOT / "videos"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_lines(path: Path) -> list[dict]:
    if not path.is_file():
        raise AssertionError(f"missing receipt: {path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def checked_sources(records: list[dict]) -> dict[str, str]:
    required = {
        (ROOT / "bin" / "manimi.pi").resolve(),
        (ROOT / "example_scene.pi").resolve(),
        (ROOT / "elliptic.pi").resolve(),
    }
    found: dict[Path, str] = {}
    for record in records:
        if record.get("schema") != "ithon.checked.v1":
            raise AssertionError(f"unexpected Ithon receipt schema: {record!r}")
        filename = Path(record["filename"])
        resolved = filename.resolve() if filename.is_absolute() else (ROOT / filename).resolve()
        if resolved in required:
            digest = sha256(resolved)
            if record.get("source_sha256") != digest:
                raise AssertionError(f"checked source digest does not match {resolved}")
            found[resolved] = digest
    missing = required - found.keys()
    if missing:
        raise AssertionError(f"render did not check: {sorted(map(str, missing))}")
    return {
        str(path.relative_to(ROOT)): digest
        for path, digest in sorted(found.items())
    }


def gpu_receipt(records: list[dict]) -> dict:
    if any(record.get("schema") != "manimi.webgpu.v1" for record in records):
        raise AssertionError("unexpected Manimi GPU receipt schema")
    devices = [record for record in records if record.get("event") == "device"]
    shaders = [record for record in records if record.get("event") == "wgsl_module"]
    if len(devices) < 2:
        raise AssertionError("both render processes must acquire a WebGPU device")
    if any(record.get("backend_request") != "Vulkan" for record in devices):
        raise AssertionError("the checked render did not request Vulkan")
    if not shaders:
        raise AssertionError("the checked render compiled no WGSL modules")
    return {
        "devices": devices,
        "wgsl_source_sha256": sorted({record["source_sha256"] for record in shaders}),
    }


def image_receipt(name: str, expected_size: tuple[int, int]) -> dict:
    path = VIDEOS / name
    with Image.open(path) as image:
        if image.format != "PNG":
            raise AssertionError(f"{name} is {image.format}, not PNG")
        if image.size != expected_size:
            raise AssertionError(f"{name} is {image.size}, not {expected_size}")
        pixels = np.asarray(image.convert("RGBA"))
    non_background = int(np.any(pixels != pixels[0, 0], axis=2).sum())
    if non_background == 0:
        raise AssertionError(f"{name} is a blank frame")
    return {
        "sha256": sha256(path),
        "size": list(expected_size),
        "non_background_pixels": non_background,
    }


def require_vulkan_log(name: str) -> None:
    log = (VIDEOS / name).read_text(encoding="utf-8")
    if "Forcing backend: Vulkan" not in log:
        raise AssertionError(f"{name} does not confirm the Vulkan backend")


def main() -> None:
    elliptic = load_checked_ithon(ROOT / "elliptic.pi", "elliptic_render_receipt")
    ithon_records = read_json_lines(Path(os.environ["ITHON_CHECK_RECEIPT"]))
    gpu_records = read_json_lines(Path(os.environ["MANIMI_GPU_RECEIPT"]))
    require_vulkan_log("ithon-circle.log")
    require_vulkan_log("elliptic-secant.log")
    receipt = {
        "schema": "manimi.checked-render.v1",
        "ithon": checked_sources(ithon_records),
        "elliptic": elliptic_semantic_receipt(elliptic),
        "webgpu": gpu_receipt(gpu_records),
        "images": {
            "ithon-circle.png": image_receipt("ithon-circle.png", (320, 180)),
            "elliptic-secant.png": image_receipt("elliptic-secant.png", (1280, 720)),
        },
    }
    output = VIDEOS / "checked-render-receipt.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
