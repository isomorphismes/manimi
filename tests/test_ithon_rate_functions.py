import importlib.util
import math
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE = ROOT / "manimlib" / "utils" / "rate_functions.py"
ITHON_SOURCE = ROOT / "manimlib" / "utils" / "rate_functions.pi"


def load_ithon_frontend():
    ithon_lib = Path(os.environ.get("ITHON_LIB", ROOT.parent / "ithon" / "Lib"))

    static_spec = importlib.util.spec_from_file_location(
        "ithon_static",
        ithon_lib / "ithon_static.py",
    )
    static_module = importlib.util.module_from_spec(static_spec)
    sys.modules["ithon_static"] = static_module
    static_spec.loader.exec_module(static_module)

    frontend_spec = importlib.util.spec_from_file_location(
        "ithon_frontend",
        ithon_lib / "ithon_frontend.py",
    )
    frontend_module = importlib.util.module_from_spec(frontend_spec)
    frontend_spec.loader.exec_module(frontend_module)
    return frontend_module


def bezier(points):
    degree = len(points) - 1

    def curve(t):
        return sum(
            point
            * math.comb(degree, index)
            * ((1 - t) ** (degree - index))
            * (t**index)
            for index, point in enumerate(points)
        )

    return curve


def execute_rate_functions(path, module_name, ithon=False):
    source = path.read_text(encoding="utf-8")
    if ithon:
        source = load_ithon_frontend().lower_source(source, str(path))
        source = (
            source.replace("←", "=")
            .replace("×", "*")
            .replace("÷", "/")
            .replace("λ", "lambda")
        )

    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


class IthonRateFunctionParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manimlib = types.ModuleType("manimlib")
        manimlib.__path__ = [str(ROOT / "manimlib")]
        utils = types.ModuleType("manimlib.utils")
        utils.__path__ = [str(ROOT / "manimlib" / "utils")]
        bezier_module = types.ModuleType("manimlib.utils.bezier")
        bezier_module.bezier = bezier
        stubs = {
            "manimlib": manimlib,
            "manimlib.utils": utils,
            "manimlib.utils.bezier": bezier_module,
        }
        with patch.dict(sys.modules, stubs):
            cls.python = execute_rate_functions(PYTHON_SOURCE, "rates_python")
            cls.ithon = execute_rate_functions(ITHON_SOURCE, "rates_ithon", ithon=True)

    def assert_close(self, left, right):
        self.assertTrue(math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12))

    def test_direct_rate_functions_match(self):
        names = (
            "linear",
            "smooth",
            "rush_into",
            "rush_from",
            "slow_into",
            "double_smooth",
            "there_and_back",
            "there_and_back_with_pause",
            "running_start",
            "overshoot",
            "wiggle",
            "lingering",
            "exponential_decay",
        )
        for name in names:
            with self.subTest(name=name):
                for value in (0.0, 0.1, 0.4, 0.5, 0.8, 1.0):
                    self.assert_close(
                        getattr(self.python, name)(value),
                        getattr(self.ithon, name)(value),
                    )

    def test_function_builders_match(self):
        python_not_quite = self.python.not_quite_there(self.python.smooth, 0.6)
        ithon_not_quite = self.ithon.not_quite_there(self.ithon.smooth, 0.6)
        python_squished = self.python.squish_rate_func(self.python.linear, 0.2, 0.7)
        ithon_squished = self.ithon.squish_rate_func(self.ithon.linear, 0.2, 0.7)

        for value in (0.0, 0.2, 0.45, 0.7, 1.0):
            self.assert_close(python_not_quite(value), ithon_not_quite(value))
            self.assert_close(python_squished(value), ithon_squished(value))

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
        for glyph in ("∈", "←", "→", "×", "÷", "λ"):
            self.assertIn(glyph, source)


if __name__ == "__main__":
    unittest.main()
