import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from tests.ithon_support import load_checked_ithon


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE = ROOT / "manimlib" / "utils" / "images.py"
ITHON_SOURCE = ROOT / "manimlib" / "utils" / "images.pi"


def execute_python(path, module_name):
    source = path.read_text(encoding="utf-8")
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


class IthonImagesParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manimlib = types.ModuleType("manimlib")
        manimlib.__path__ = [str(ROOT / "manimlib")]
        utils = types.ModuleType("manimlib.utils")
        utils.__path__ = [str(ROOT / "manimlib" / "utils")]

        directories = types.ModuleType("manimlib.utils.directories")
        directories.get_raster_image_dir = lambda: "/raster"
        directories.get_vector_image_dir = lambda: "/vector"
        directories.get_three_d_model_dir = lambda: "/model"

        file_ops = types.ModuleType("manimlib.utils.file_ops")

        def find_file(file_name, directories=None, extensions=None):
            return f"{file_name}|{directories!r}|{extensions!r}"

        file_ops.find_file = find_file

        image_module = types.ModuleType("PIL.Image")
        image_module.fromarray = lambda array: np.array(array, copy=True)
        pil = types.ModuleType("PIL")
        pil.Image = image_module

        stubs = {
            "manimlib": manimlib,
            "manimlib.utils": utils,
            "manimlib.utils.directories": directories,
            "manimlib.utils.file_ops": file_ops,
            "PIL": pil,
            "PIL.Image": image_module,
        }
        with patch.dict(sys.modules, stubs):
            cls.python = execute_python(PYTHON_SOURCE, "images_python")
            cls.ithon = load_checked_ithon(ITHON_SOURCE, "images_ithon")

    def test_path_helpers_match(self):
        for name, value in (
            ("get_full_raster_image_path", "portrait"),
            ("get_full_vector_image_path", "diagram"),
            ("get_full_three_d_model_path", "torus"),
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    getattr(self.python, name)(value),
                    getattr(self.ithon, name)(value),
                )

    def test_invert_image_matches(self):
        image = np.array([[0, 64], [128, 255]], dtype=np.uint8)
        np.testing.assert_array_equal(
            self.python.invert_image(image),
            self.ithon.invert_image(image),
        )

    def test_public_names_match(self):
        python_names = {
            name for name in self.python.__dict__ if not name.startswith("_")
        }
        ithon_names = {
            name for name in self.ithon.__dict__ if not name.startswith("_")
        }
        self.assertEqual(python_names, ithon_names)

    def test_source_uses_ithon_syntax(self):
        source = ITHON_SOURCE.read_text(encoding="utf-8")
        for glyph in ("∈", "←", "→"):
            self.assertIn(glyph, source)

    def test_parity_module_uses_ithon_runtime_loader(self):
        self.assertEqual(type(self.ithon.__loader__).__name__, "IthonSourceLoader")


if __name__ == "__main__":
    unittest.main()
