import numpy as np


def elliptic_semantic_receipt(scene) -> dict:
    curve = {
        "P": scene.elliptic_equation(scene.p_x, scene.p_y),
        "Q": scene.elliptic_equation(scene.q_x, scene.q_y),
        "-(P+Q)": scene.elliptic_equation(
            scene.minus_sum_x,
            scene.minus_sum_y,
        ),
        "P+Q": scene.elliptic_equation(scene.sum_x, scene.sum_y),
    }
    secant = scene.secant_residual(
        scene.p_x,
        scene.p_y,
        scene.q_x,
        scene.q_y,
        scene.minus_sum_x,
        scene.minus_sum_y,
    )
    reflection = {
        "x": scene.reflection_x_residual(scene.minus_sum_x, scene.sum_x),
        "y": scene.reflection_y_residual(scene.minus_sum_y, scene.sum_y),
    }
    expected_sum = np.array([
        scene.minus_sum_x,
        -scene.minus_sum_y,
        0.0,
    ])
    sum_coordinates = float(np.max(np.abs(scene.sum_point - expected_sum)))
    residuals = [*curve.values(), secant, *reflection.values(), sum_coordinates]
    if any(abs(value) > scene.geometry_tolerance for value in residuals):
        raise AssertionError(
            f"elliptic construction exceeds tolerance {scene.geometry_tolerance}: "
            f"{residuals}"
        )
    return {
        "tolerance": scene.geometry_tolerance,
        "curve_residuals": curve,
        "secant_residual": secant,
        "reflection_residuals": reflection,
        "sum_coordinate_residual": sum_coordinates,
    }
