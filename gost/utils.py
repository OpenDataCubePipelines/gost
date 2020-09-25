"""
A temporary script that at least fleshes out some basic stats/tests
that might be useful.
Once a new direction has been sorted out, this and other accompanying
scripts will be designed and executed properly.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Union
import attr
import numpy  # type: ignore

from idl_functions import histogram  # type: ignore

from gost.odc_documents import Granule, Measurement


class FmaskThemes(Enum):
    """
    Defines the class schema used by the Fmask datasets.
    """

    NULL = 0
    CLEAR = 1
    CLOUD = 2
    CLOUD_SHADOW = 3
    SNOW = 4
    WATER = 5


class ContiguityThemes(Enum):
    """
    Defines the class schema used by the contiguity datasets.
    """

    NON_CONTIGUOUS = 0
    CONTIGUOUS = 1


class TerrainShadowThemes(Enum):
    """
    Defines the class schema used by the terrain shadow datasets.
    """

    SHADED = 0
    UNSHADED = 1


@attr.s()
class MeasurementRecords:
    """
    Base class for holding the measurement dataset evaluation results.
    """

    granule: List = attr.ib(default=attr.Factory(list))
    reference_fname: List = attr.ib(default=attr.Factory(list))
    test_fname: List = attr.ib(default=attr.Factory(list))
    measurement: List = attr.ib(default=attr.Factory(list))
    size: List = attr.ib(default=attr.Factory(list))
    region_code: List = attr.ib(default=attr.Factory(list))

    def add_base_info(
        self,
        reference_document: Granule,
        pathname_reference: Path,
        pathname_test: Path,
        size: int,
        measurement: str,
    ) -> None:
        """Add the base information for a given record."""
        self.granule.append(reference_document.granule_id)
        self.reference_fname.append(str(pathname_reference))
        self.test_fname.append(str(pathname_test))
        self.measurement.append(measurement)
        self.size.append(size)
        self.region_code.append(reference_document.region_code)

    def records(self):
        """
        Converts the class attributes and their values to a dict.
        """
        return attr.asdict(self)


@attr.s()
class GeneralRecords(MeasurementRecords):
    """
    Placeholder for the general columns/fields and the list of records
    they'll contain.
    """

    min_residual: List = attr.ib(default=attr.Factory(list))
    max_residual: List = attr.ib(default=attr.Factory(list))
    percent_different: List = attr.ib(default=attr.Factory(list))
    percentile_90: List = attr.ib(default=attr.Factory(list))
    percentile_99: List = attr.ib(default=attr.Factory(list))
    percent_data_2_null: List = attr.ib(default=attr.Factory(list))
    percent_null_2_data: List = attr.ib(default=attr.Factory(list))
    mean_residual: List = attr.ib(default=attr.Factory(list))
    standard_deviation: List = attr.ib(default=attr.Factory(list))
    skewness: List = attr.ib(default=attr.Factory(list))
    kurtosis: List = attr.ib(default=attr.Factory(list))
    max_absolute: List = attr.ib(default=attr.Factory(list))


def _make_thematic_class(themes, name):
    """Class constructor for thematic datasets."""

    result = attr.make_class(
        name,
        {
            f"{theme.name.lower()}_2_{theme2.name.lower()}": attr.ib(
                default=attr.Factory(list)
            )
            for theme in themes
            for theme2 in themes
        },
        bases=(MeasurementRecords,),
    )

    return result


FmaskRecords = _make_thematic_class(FmaskThemes, "FmaskRecords")
ContiguityRecords = _make_thematic_class(ContiguityThemes, "ContiguityRecords")
TerrainShadowRecords = _make_thematic_class(TerrainShadowThemes, "TerrainShadowRecords")


def evaluate_themes(
    ref_measurement: Measurement,
    test_measurement: Measurement,
    themes: Union[FmaskThemes, ContiguityThemes, TerrainShadowThemes],
) -> Dict[str, float]:
    """
    A generic tool for evaluating thematic datasets.
    """
    values = [v.value for v in themes]
    n_values = len(values)
    minv = min(values)
    maxv = max(values)

    # read data and reshape to 1D
    ref_data = ref_measurement.read().ravel()
    test_data = test_measurement.read().ravel()

    ref_h = histogram(ref_data, minv=minv, maxv=maxv, reverse_indices="ri")

    ref_hist = ref_h["histogram"]
    ref_ri = ref_h["ri"]

    theme_changes = dict()

    for theme in themes:
        i = theme.value
        # check we have data for this category
        if ref_hist[i] == 0:
            # no changes as nothing exists in the reference data
            theme_changes[theme] = numpy.full((n_values,), numpy.nan)
            continue
        idx = ref_ri[ref_ri[i] : ref_ri[i + 1]]
        values = test_data[idx]
        h = histogram(values, minv=minv, maxv=maxv)
        hist = h["histogram"]
        pdf = hist / numpy.sum(hist)
        theme_changes[theme] = pdf * 100

    # split outputs into separate records
    result = dict()
    for theme in themes:
        for theme2 in themes:
            key = f"{theme.name.lower()}_2_{theme2.name.lower()}"
            result[key] = theme_changes[theme][theme2.value]

    return result


def data_mask(measurement: Measurement) -> numpy.ndarray:
    """Extract a mask of data and no data; handle a couple of cases."""
    nodata = measurement.nodata
    if nodata is None:
        nodata = 0
    is_finite = numpy.isfinite(nodata)

    if is_finite:
        mask = measurement.read() != nodata
    else:
        mask = numpy.isfinite(measurement.read())

    return mask, nodata


def evaluate(
    ref_measurement: Measurement, test_measurement: Measurement
) -> numpy.ndarray:
    """A basic difference operator where data exists at both index locations"""
    ref_mask, _ = data_mask(ref_measurement)
    test_mask, _ = data_mask(test_measurement)

    # evaluate only where valid data locations are the same
    mask = ref_mask & test_mask
    result = ref_measurement.read()[mask] - test_measurement.read()[mask]

    return result


def evaluate_nulls(
    ref_measurement: Measurement, test_measurement: Measurement
) -> Tuple[float, float]:
    """
    A basic eval for checking if null locations have changed.
    eg, data pixel to null pixel and vice versa.
    """
    mask, nodata = data_mask(ref_measurement)
    is_finite = numpy.isfinite(nodata)

    # read data from both the data and nodata masks
    values = test_measurement.read()[mask]
    values2 = test_measurement.read()[~mask]

    if is_finite:
        valid_2_null = values == nodata
        null_2_valid = values2 != nodata
    else:
        valid_2_null = ~numpy.isfinite(values)
        null_2_valid = numpy.isfinite(values2)

    # determine pixels that have changed from valid -> null & vice versa
    valid_2_null_pct = valid_2_null.sum() / mask.size
    null_2_valid_pct = null_2_valid.sum() / mask.size
    # trial count instead of percent
    # valid_2_null_pct = valid_2_null.sum()
    # null_2_valid_pct = null_2_valid.sum()

    return valid_2_null_pct, null_2_valid_pct
