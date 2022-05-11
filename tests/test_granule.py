import math
from typing import Dict, List
import pytest

from gost.odc_documents import load_odc_metadata, load_proc_info
from gost.data_model import Granule, GranuleProcInfo
from . import LS5_ODC_DOC_PATH, LS7_ODC_DOC_PATH, LS8_ODC_DOC_PATH
from . import LS5_ODC_PROC_PATH, LS7_ODC_PROC_PATH, LS8_ODC_PROC_PATH


NaN = math.nan
LS5_GRN = load_odc_metadata(LS5_ODC_DOC_PATH)
LS7_GRN = load_odc_metadata(LS7_ODC_DOC_PATH)
LS8_GRN = load_odc_metadata(LS8_ODC_DOC_PATH)
LS5_PROC = load_proc_info(LS5_ODC_PROC_PATH)
LS7_PROC = load_proc_info(LS7_ODC_PROC_PATH)
LS8_PROC = load_proc_info(LS8_ODC_PROC_PATH)


def _check_nan(a, b):
    if not math.isnan(a):
        result = a == b
    else:
        result = math.isnan(a) == math.isnan(b)

    return result


@pytest.mark.parametrize(
    "granule, expected_result", [(LS5_GRN, "WRS2"), (LS7_GRN, "WRS2"), (LS8_GRN, "WRS2")]
)
def test_framing(granule: Granule, expected_result: str):
    """Check that the framing code name is correct."""
    assert granule.framing == expected_result


@pytest.mark.parametrize(
    "granule, expected_result",
    [
        (LS5_GRN, "LT50920842008269ASA00"),
        (LS7_GRN, "LE70920802020342ASA00"),
        (LS8_GRN, "LC80900832020208LGN00"),
    ],
)
def test_granule_id(granule: Granule, expected_result: str):
    """Check that the granule id is correct."""
    assert granule.granule_id == expected_result


@pytest.mark.parametrize(
    "granule, expected_result",
    [
        (LS5_GRN, "cfee8e34-2fb5-5aab-bec9-4312a7175849"),
        (LS7_GRN, "44c60952-6745-57c6-b9ab-4d1d6fb559ad"),
        (LS8_GRN, "438a0c9d-d327-53ae-9a55-f38851f689e3"),
    ],
)
def test_parent_uuid(granule: Granule, expected_result: str):
    """Check that the parent uuid is correct."""
    assert granule.parent_uuid == expected_result


@pytest.mark.parametrize(
    "granule, expected_result",
    [(LS5_GRN, "092084"), (LS7_GRN, "092080"), (LS8_GRN, "090083")],
)
def test_region_code(granule: Granule, expected_result: str):
    """Check that the region code is correct."""
    assert granule.region_code == expected_result


@pytest.mark.parametrize(
    "granule, expected_result",
    [(LS5_GRN, "ga_ls5t_ard_3"), (LS7_GRN, "ga_ls7e_ard_3"), (LS8_GRN, "ga_ls8c_ard_3")],
)
def test_product_name(granule: Granule, expected_result: str):
    """Check that the product name is correct."""
    assert granule.product_name == expected_result


@pytest.mark.parametrize(
    "granule, expected_result", [(LS5_GRN, 27), (LS7_GRN, 29), (LS8_GRN, 31)]
)
def test_number_of_measurements(granule: Granule, expected_result: int):
    """Check that the number of measurements is correct."""
    assert len(granule.measurements) == expected_result


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (
            LS5_PROC,
            {
                "colour_blue": 1,
                "colour_green": 73,
                "colour_red": 0,
                "colour_teal": 13,
                "colour_yellow": 0,
            },
        ),
        (
            LS7_PROC,
            {
                "colour_blue": 3,
                "colour_green": 113,
                "colour_red": 0,
                "colour_teal": 48,
                "colour_yellow": 2,
            },
        ),
        (
            LS8_PROC,
            {
                "colour_blue": 0,
                "colour_green": 0,
                "colour_red": 0,
                "colour_teal": 0,
                "colour_yellow": 0,
            },
        ),
    ],
)
def test_gqa_colors(granule_proc: GranuleProcInfo, expected_result: Dict[str, int]):
    """Check that the gqa color distribution is correct."""
    assert granule_proc.geometric_quality.colors.flatten() == expected_result


@pytest.mark.parametrize(
    "granule_proc, expected_result", [(LS5_PROC, 56), (LS7_PROC, 124), (LS8_PROC, 0)]
)
def test_gqa_final_qa_count(granule_proc: GranuleProcInfo, expected_result: int):
    """Check that the gqa final point count is correct."""
    assert granule_proc.geometric_quality.final_qa_count == expected_result


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, "no errors"),
        (LS7_PROC, "no errors"),
        (LS8_PROC, "no errors; no QA points can be matched"),
    ],
)
def test_gqa_error_msg(granule_proc: GranuleProcInfo, expected_result: str):
    """Check that the gqa error message is correct."""
    assert granule_proc.geometric_quality.error_message == expected_result


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, "2014-03-19T00:00:00+00:00"),
        (LS7_PROC, "2014-05-22T00:00:00+00:00"),
        (LS8_PROC, "2013-09-09T00:00:00+00:00"),
    ],
)
def test_gqa_ref_date(granule_proc: GranuleProcInfo, expected_result: str):
    """Check that the gqa reference date is correct."""
    assert granule_proc.geometric_quality.ref_date == expected_result


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, [0.11, 0.16, 0.2]),
        (LS7_PROC, [0.21, 0.17, 0.27]),
        (LS8_PROC, [NaN, NaN, NaN]),
    ],
)
def test_gqa_abs_iterative_mean(
    granule_proc: GranuleProcInfo, expected_result: List[float]
):
    """Check that the gqa abs iterative mean is correct."""
    assert _check_nan(
        granule_proc.geometric_quality.residual.abs_iterative_mean.x, expected_result[0]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.abs_iterative_mean.y, expected_result[1]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.abs_iterative_mean.xy, expected_result[2]
    )


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, [0.19, 0.21, 0.28]),
        (LS7_PROC, [0.29, 0.27, 0.4]),
        (LS8_PROC, [NaN, NaN, NaN]),
    ],
)
def test_gqa_abs(granule_proc: GranuleProcInfo, expected_result: List[float]):
    """Check that the gqa abs is correct."""
    assert _check_nan(granule_proc.geometric_quality.residual.abs.x, expected_result[0])
    assert _check_nan(granule_proc.geometric_quality.residual.abs.y, expected_result[1])
    assert _check_nan(granule_proc.geometric_quality.residual.abs.xy, expected_result[2])


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, [-0.08, 0.15, 0.17]),
        (LS7_PROC, [-0.2, 0.11, 0.22]),
        (LS8_PROC, [NaN, NaN, NaN]),
    ],
)
def test_gqa_iterative_mean(granule_proc: GranuleProcInfo, expected_result: List[float]):
    """Check that the gqa iterative mean is correct."""
    assert _check_nan(
        granule_proc.geometric_quality.residual.iterative_mean.x, expected_result[0]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.iterative_mean.y, expected_result[1]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.iterative_mean.xy, expected_result[2]
    )


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, [0.11, 0.11, 0.15]),
        (LS7_PROC, [0.16, 0.18, 0.24]),
        (LS8_PROC, [NaN, NaN, NaN]),
    ],
)
def test_gqa_iterative_stddev(
    granule_proc: GranuleProcInfo, expected_result: List[float]
):
    """Check that the gqa iterative standard deviation is correct."""
    assert _check_nan(
        granule_proc.geometric_quality.residual.iterative_stddev.x, expected_result[0]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.iterative_stddev.y, expected_result[1]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.iterative_stddev.xy, expected_result[2]
    )


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, [-0.11, 0.13, 0.17]),
        (LS7_PROC, [-0.19, 0.12, 0.22]),
        (LS8_PROC, [NaN, NaN, NaN]),
    ],
)
def test_gqa_mean(granule_proc: GranuleProcInfo, expected_result: List[float]):
    """Check that the gqa mean is correct."""
    assert _check_nan(granule_proc.geometric_quality.residual.mean.x, expected_result[0])
    assert _check_nan(granule_proc.geometric_quality.residual.mean.y, expected_result[1])
    assert _check_nan(granule_proc.geometric_quality.residual.mean.xy, expected_result[2])


@pytest.mark.parametrize(
    "granule_proc, expected_result",
    [
        (LS5_PROC, [0.24, 0.24, 0.34]),
        (LS7_PROC, [0.37, 0.4, 0.55]),
        (LS8_PROC, [NaN, NaN, NaN]),
    ],
)
def test_gqa_stddev(granule_proc: GranuleProcInfo, expected_result: List[float]):
    """Check that the gqa standard deviation is correct."""
    assert _check_nan(
        granule_proc.geometric_quality.residual.stddev.x, expected_result[0]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.stddev.y, expected_result[1]
    )
    assert _check_nan(
        granule_proc.geometric_quality.residual.stddev.xy, expected_result[2]
    )


@pytest.mark.parametrize(
    "granule_proc, expected_result", [(LS5_PROC, 0.34), (LS7_PROC, 0.5), (LS8_PROC, NaN)]
)
def test_gqa_cep90(granule_proc: GranuleProcInfo, expected_result: float):
    """Check that the gqa circular error probable is correct."""
    assert _check_nan(granule_proc.geometric_quality.residual.cep90, expected_result)
