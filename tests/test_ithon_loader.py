import importlib.machinery
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module_loader():
    package = types.ModuleType("manimlib")
    package.__path__ = [str(ROOT / "manimlib")]

    config = types.ModuleType("manimlib.config")
    config.manim_config = types.SimpleNamespace(
        ignore_manimlib_modules_on_reload=False,
    )

    logger = types.ModuleType("manimlib.logger")
    logger.log = types.SimpleNamespace(debug=lambda *args, **kwargs: None)

    modules = {
        "manimlib": package,
        "manimlib.config": config,
        "manimlib.logger": logger,
    }
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(
            "manimlib.module_loader",
            ROOT / "manimlib" / "module_loader.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.ModuleLoader


class FakeIthonSourceLoader(importlib.machinery.SourceFileLoader):
    pass


class IthonModuleLoaderTest(unittest.TestCase):
    def setUp(self):
        self.module_loader = load_module_loader()

    def test_pi_uses_ithon_source_loader(self):
        ithon_run = types.ModuleType("ithon_run")
        ithon_run.IthonSourceLoader = FakeIthonSourceLoader

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "checked_scene.pi"
            source.write_text("answer = 42\n", encoding="utf-8")
            with patch.dict(sys.modules, {"ithon_run": ithon_run}):
                module = self.module_loader.get_module(str(source))

        self.assertEqual(module.answer, 42)
        self.assertIsInstance(module.__loader__, FakeIthonSourceLoader)
        self.assertTrue(module.__name__.endswith("checked_scene"))

    def test_pi_rejects_plain_python_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "scene.pi"
            source.write_text("answer = 42\n", encoding="utf-8")
            with patch.dict(sys.modules, {"ithon_run": None}):
                with self.assertRaisesRegex(RuntimeError, "run ./bin/manimi"):
                    self.module_loader.get_module(str(source))

    def test_python_scene_loading_remains_available(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "python_scene.py"
            source.write_text("answer = 42\n", encoding="utf-8")
            module = self.module_loader.get_module(str(source))

        self.assertEqual(module.answer, 42)
        self.assertTrue(module.__name__.endswith("python_scene"))

    def test_unknown_source_extension_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must use .pi or .py"):
            self.module_loader._get_spec("scene", "scene.txt")


if __name__ == "__main__":
    unittest.main()
