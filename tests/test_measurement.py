from typing import Tuple
import pytest
from affine import Affine

from gost.odc_documents import load_odc_metadata
from gost.data_model import Granule
from . import LS5_ODC_DOC_PATH, LS7_ODC_DOC_PATH, LS8_ODC_DOC_PATH

LS5_GRN = load_odc_metadata(LS5_ODC_DOC_PATH)
LS7_GRN = load_odc_metadata(LS7_ODC_DOC_PATH)
LS8_GRN = load_odc_metadata(LS8_ODC_DOC_PATH)


@pytest.mark.parametrize(
    "granule, measurement_name, expected_result",
    [
        (LS5_GRN, "oa_fmask", (7091, 7981)),
        (LS7_GRN, "oa_fmask", (7131, 8271)),
        (LS8_GRN, "oa_fmask", (7691, 7621)),
    ],
)
def test_measurement_shape(
    granule: Granule, measurement_name: str, expected_result: Tuple[int, int]
):
    """Check that the measurement shape is correct."""
    assert granule.measurements[measurement_name].shape == expected_result


@pytest.mark.parametrize(
    "granule, measurement_name, expected_result",
    [
        (
            LS5_GRN,
            "oa_fmask",
            Affine.from_gdal(*(358185.0, 30.0, 0.0, -3724785.0, 0.0, -30.0)),
        ),
        (
            LS7_GRN,
            "oa_fmask",
            Affine.from_gdal(*(508785.0, 30.0, 0.0, -3088185.0, 0.0, -30.0)),
        ),
        (
            LS8_GRN,
            "oa_fmask",
            Affine.from_gdal(*(128085.0, 30.0, 0.0, -3559185.0, 0.0, -30.0)),
        ),
    ],
)
def test_measurement_transform(
    granule: Granule, measurement_name: str, expected_result: Affine
):
    """Check that the measurement transform is correct."""
    assert granule.measurements[measurement_name].transform == expected_result


@pytest.mark.parametrize(
    "granule, measurement_name, expected_result",
    [
        (LS5_GRN, "oa_fmask", True),
        (LS7_GRN, "oa_fmask", True),
        (LS8_GRN, "oa_fmask", True),
    ],
)
def test_measurement_closed(
    granule: Granule, measurement_name: str, expected_result: bool
):
    """Check that the measurement file handler is closed."""
    assert granule.measurements[measurement_name].closed == expected_result
