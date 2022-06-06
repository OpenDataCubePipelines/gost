import numpy
import structlog

from gost.utils import evaluate, evaluate_themes, evaluate_nulls, FmaskThemes
from gost.data_model import Measurement

_LOG = structlog.get_logger("fmask")


def test_evaluate_themes_identical(
    ref_fmask_measurement1: Measurement, test_fmask_measurement1: Measurement
):
    """Test that the result indicates no pixel has changed categorical state."""
    truth = {
        "null_2_null": 100.0,
        "null_2_clear": 0.0,
        "null_2_cloud": 0.0,
        "null_2_cloud_shadow": 0.0,
        "null_2_snow": 0.0,
        "null_2_water": 0.0,
        "clear_2_null": 0.0,
        "clear_2_clear": 100.0,
        "clear_2_cloud": 0.0,
        "clear_2_cloud_shadow": 0.0,
        "clear_2_snow": 0.0,
        "clear_2_water": 0.0,
        "cloud_2_null": 0.0,
        "cloud_2_clear": 0.0,
        "cloud_2_cloud": 100.0,
        "cloud_2_cloud_shadow": 0.0,
        "cloud_2_snow": 0.0,
        "cloud_2_water": 0.0,
        "cloud_shadow_2_null": 0.0,
        "cloud_shadow_2_clear": 0.0,
        "cloud_shadow_2_cloud": 0.0,
        "cloud_shadow_2_cloud_shadow": 100.0,
        "cloud_shadow_2_snow": 0.0,
        "cloud_shadow_2_water": 0.0,
        "snow_2_null": 0.0,
        "snow_2_clear": 0.0,
        "snow_2_cloud": 0.0,
        "snow_2_cloud_shadow": 0.0,
        "snow_2_snow": 100.0,
        "snow_2_water": 0.0,
        "water_2_null": 0.0,
        "water_2_clear": 0.0,
        "water_2_cloud": 0.0,
        "water_2_cloud_shadow": 0.0,
        "water_2_snow": 0.0,
        "water_2_water": 100.0,
    }
    result = evaluate_themes(ref_fmask_measurement1, test_fmask_measurement1, FmaskThemes)
    assert result == truth


def test_evaluate_themes_change(
    ref_fmask_measurement2: Measurement, test_fmask_measurement3: Measurement
):
    """Test that the result indicates pixels have changed categorical state."""
    truth = {
        "null_2_null": 28.57142857142857,
        "null_2_clear": 14.285714285714285,
        "null_2_cloud": 14.285714285714285,
        "null_2_cloud_shadow": 14.285714285714285,
        "null_2_snow": 14.285714285714285,
        "null_2_water": 14.285714285714285,
        "clear_2_null": 14.285714285714285,
        "clear_2_clear": 28.57142857142857,
        "clear_2_cloud": 14.285714285714285,
        "clear_2_cloud_shadow": 14.285714285714285,
        "clear_2_snow": 14.285714285714285,
        "clear_2_water": 14.285714285714285,
        "cloud_2_null": 14.285714285714285,
        "cloud_2_clear": 14.285714285714285,
        "cloud_2_cloud": 28.57142857142857,
        "cloud_2_cloud_shadow": 14.285714285714285,
        "cloud_2_snow": 14.285714285714285,
        "cloud_2_water": 14.285714285714285,
        "cloud_shadow_2_null": 14.285714285714285,
        "cloud_shadow_2_clear": 14.285714285714285,
        "cloud_shadow_2_cloud": 14.285714285714285,
        "cloud_shadow_2_cloud_shadow": 28.57142857142857,
        "cloud_shadow_2_snow": 14.285714285714285,
        "cloud_shadow_2_water": 14.285714285714285,
        "snow_2_null": 14.285714285714285,
        "snow_2_clear": 14.285714285714285,
        "snow_2_cloud": 14.285714285714285,
        "snow_2_cloud_shadow": 14.285714285714285,
        "snow_2_snow": 28.57142857142857,
        "snow_2_water": 14.285714285714285,
        "water_2_null": 14.285714285714285,
        "water_2_clear": 14.285714285714285,
        "water_2_cloud": 14.285714285714285,
        "water_2_cloud_shadow": 14.285714285714285,
        "water_2_snow": 14.285714285714285,
        "water_2_water": 28.57142857142857,
    }
    result = evaluate_themes(ref_fmask_measurement2, test_fmask_measurement3, FmaskThemes)
    assert result == truth


def test_evaluate_nulls(
    ref_reflectance_measurement: Measurement, test_reflectance_measurement1: Measurement
):
    """Test that the two measurements have identical null locations"""
    v_2_null, null_2_v = evaluate_nulls(
        ref_reflectance_measurement, test_reflectance_measurement1
    )
    assert v_2_null == 0.0
    assert null_2_v == 0.0


def test_evaluate_nulls_change(
    ref_reflectance_measurement: Measurement, test_reflectance_measurement2: Measurement
):
    """Test that the two measurements have different null locations"""
    v_2_null, null_2_v = evaluate_nulls(
        ref_reflectance_measurement, test_reflectance_measurement2
    )
    assert v_2_null == 0.25
    assert null_2_v == 0.125


def test_evaluate_reflectance(
    ref_reflectance_measurement: Measurement, test_reflectance_measurement2: Measurement
):
    """Test that the two measurements return zero difference for all pixels."""
    result = evaluate(ref_reflectance_measurement, test_reflectance_measurement2)
    assert numpy.count_nonzero(result) == 0


def test_evaluate_reflectance_change(
    ref_reflectance_measurement: Measurement, test_reflectance_measurement3: Measurement
):
    """Test that the two measurements have all different values."""
    result = evaluate(ref_reflectance_measurement, test_reflectance_measurement3)
    assert numpy.count_nonzero(result) == 8
