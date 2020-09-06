"""
A temporary script that at least fleshes out some basic stats/tests
that might be useful.
Once a new direction has been sorted out, this and other accompanying
scripts will be designed and executed properly.
"""

from enum import Enum
from pathlib import Path
import numpy  # type: ignore
from typing import Any, Dict, List, Tuple, Union

from idl_functions import histogram  # type: ignore

from gost.odc_documents import Granule, Measurement


FMT: str = "{}_2_{}"


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


class Records:
    def __init__(self):
        self.granule = []
        self.reference_fname = []
        self.test_fname = []
        self.measurement = []
        self.size = []
        self.region_code = []

    @property
    def records(self) -> Dict[str, List[Any]]:
        return self.__dict__

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


class GeneralRecords(Records):
    """
    Placeholder for the general columns/fields and the list of records
    they'll contain.
    """

    def __init__(self):
        super(GeneralRecords, self).__init__()

        self.min_residual = []
        self.max_residual = []
        self.percent_different = []
        self.percentile_90 = []
        self.percentile_99 = []
        self.percent_data_2_null = []
        self.percent_null_2_data = []
        self.mean_residual = []
        self.standard_deviation = []
        self.skewness = []
        self.kurtosis = []


class ThematicRecords(Records):
    """
    Base class for defining the columns/fields for the thematic
    datasets and the list of records they'll contain.
    """

    def __init__(self, categories):
        super(ThematicRecords, self).__init__()

        for category in categories:
            for category2 in categories:
                name = FMT.format(category.name.lower(), category2.name.lower())
                setattr(self, name, [])


class FmaskRecords(ThematicRecords):
    """
    Placeholder for the fmask columns/fields and the list of records
    they'll contain.
    """

    def __init__(self):
        super(FmaskRecords, self).__init__(FmaskThemes)


class ContiguityRecords(ThematicRecords):
    """
    Placeholder for the contiguity columns/fields and the list of
    records they'll contain.
    """

    def __init__(self):
        super(ContiguityRecords, self).__init__(ContiguityThemes)


class TerrainShadowRecords(ThematicRecords):
    """
    Placeholder for the terrain shadow columns/fields and the list of
    records they'll contain.
    """

    def __init__(self):
        super(TerrainShadowRecords, self).__init__(TerrainShadowThemes)


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
        fmt = "{}_2_{}"
        for theme2 in themes:
            key = fmt.format(theme.name.lower(), theme2.name.lower())
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
