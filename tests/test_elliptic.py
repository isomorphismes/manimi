import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from tests.elliptic_semantics import elliptic_semantic_receipt
from tests.ithon_support import load_checked_ithon


ROOT = Path(__file__).resolve().parents[1]
ELLIPTIC_SOURCE = ROOT / "elliptic.pi"


class ForeignScene:
    pass


def foreign_manimlib() -> types.ModuleType:
    module = types.ModuleType("manimlib")
    module.Scene = ForeignScene
    for name in ("Dot", "ImplicitFunction", "Line", "Tex"):
        setattr(module, name, type(name, (), {}))
    for name in (
        "BLUE",
        "DL",
        "DR",
        "GREEN",
        "GREY_B",
        "RED",
        "TEAL_B",
        "UL",
        "UR",
        "YELLOW",
    ):
        setattr(module, name, object())
    return module


class EllipticConstructionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict("sys.modules", {"manimlib": foreign_manimlib()}):
            cls.scene = load_checked_ithon(ELLIPTIC_SOURCE, "elliptic_checked_test")
        cls.receipt = elliptic_semantic_receipt(cls.scene)

    def assert_residual(self, residual):
        self.assertLessEqual(abs(residual), self.scene.geometry_tolerance)

    def test_real_ithon_loader_checked_the_render_source(self):
        self.assertEqual(type(self.scene.__loader__).__name__, "IthonSourceLoader")

    def test_all_named_points_lie_on_the_curve(self):
        for name, residual in self.receipt["curve_residuals"].items():
            with self.subTest(point=name):
                self.assert_residual(residual)

    def test_p_q_and_minus_sum_share_one_secant(self):
        self.assert_residual(self.receipt["secant_residual"])

    def test_rendered_secant_contains_the_named_intersections(self):
        for name, residual in self.receipt["rendered_secant_residuals"].items():
            with self.subTest(point=name):
                self.assert_residual(residual)

    def test_sum_is_the_x_axis_reflection_of_minus_sum(self):
        self.assert_residual(self.receipt["reflection_residuals"]["x"])
        self.assert_residual(self.receipt["reflection_residuals"]["y"])
        np.testing.assert_allclose(
            self.scene.sum_point,
            np.array([self.scene.minus_sum_x, -self.scene.minus_sum_y, 0.0]),
            rtol=0.0,
            atol=self.scene.geometry_tolerance,
        )


if __name__ == "__main__":
    unittest.main()
