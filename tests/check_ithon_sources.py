from pathlib import Path

from ithon_frontend import check_file


root = Path(__file__).resolve().parents[1]
sources = (
    root / "bin" / "manimi.pi",
    root / "example_scene.pi",
    root / "elliptic.pi",
    root / "manimlib" / "utils" / "rate_functions.pi",
    root / "manimlib" / "utils" / "images.pi",
)

for source in sources:
    check_file(str(source))
    print(source.relative_to(root))
