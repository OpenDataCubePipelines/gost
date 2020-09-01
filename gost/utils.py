"""
A temporary script that at least fleshes out some basic stats/tests
that might be useful.
Once a new direction has been sorted out, this and other accompanying
scripts will be designed and executed properly.
"""

from enum import Enum
import numpy
from typing import Any, Dict, List, Tuple, Union
import rasterio

from idl_functions import histogram


FMT: str = "{}_2_{}"


class FmaskCategories(Enum):
    """
    Defines the class schema used by the Fmask datasets.
    """

    NULL = 0
    CLEAR = 1
    CLOUD = 2
    CLOUD_SHADOW = 3
    SNOW = 4
    WATER = 5


class ContiguityCategories(Enum):
    """
    Defines the class schema used by the contiguity datasets.
    """

    NON_CONTIGUOUS = 0
    CONTIGUOUS = 1


class TerrainShadowCategories(Enum):
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
    def records(self) -> Dict[str, List[Any, ...]]:
        return self.__dict__


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


class CategoricalRecords(Records):
    """
    Base class for defining the columns/fields for the categorical
    datasets and the list of records they'll contain.
    """

    def __init__(self, categories):
        super(CategoricalRecords, self).__init__()

        for category in categories:
            for category2 in categories:
                name = FMT.format(category.name.lower(), category2.name.lower())
                setattr(self, name, [])


class FmaskRecords(CategoricalRecords):
    """
    Placeholder for the fmask columns/fields and the list of records
    they'll contain.
    """

    def __init__(self):
        super(FmaskRecords, self).__init__(FmaskCategories)


class ContiguityRecords(CategoricalRecords):
    """
    Placeholder for the contiguity columns/fields and the list of
    records they'll contain.
    """

    def __init__(self):
        super(ContiguityRecords, self).__init__(ContiguityCategories)


class TerrainShadowRecords(CategoricalRecords):
    """
    Placeholder for the terrain shadow columns/fields and the list of
    records they'll contain.
    """

    def __init__(self):
        super(TerrainShadowRecords, self).__init__(TerrainShadowCategories)


def evaluate(
    ref_ds: rasterio.io.DatasetReader, test_ds: rasterio.io.DatasetReader
) -> numpy.ndarray:
    """
    A basic implementation of a difference operator.
    """
    if ref_ds.dtypes[0] == "bool":
        result = numpy.logical_xor(ref_ds.read(1), ref_ds.read(1)).astype("uint8")
    else:
        result = ref_ds.read(1) - test_ds.read(1)
    return result


def evaluate_fmask(
    ref_ds: rasterio.io.DatasetReader, test_ds: rasterio.io.DatasetReader
) -> Dict[str, float]:
    """
    A basic tool to evaluate each category of Fmask and build a
    distribution of category change. eg what pixels were identified as
    cloud and now as clear, water, cloud shadow, snow.
    """
    # fmask category limits
    minv = FmaskCategories.NULL.value
    maxv = FmaskCategories.WATER.value

    # read data and reshape to 1D
    ref_data = ref_ds.read(1).ravel()
    test_data = test_ds.read(1).ravel()

    ref_h = histogram(ref_data, minv=minv, maxv=maxv, reverse_indices="ri")

    ref_hist = ref_h["histogram"]
    ref_ri = ref_h["ri"]

    category_changes = dict()

    for category in FmaskCategories:
        i = category.value
        # check we have data for this category
        if ref_hist[i] == 0:
            # no changes as nothing exists in the reference data
            category_changes[category] = numpy.zeros((6,), dtype="int")
            continue

        idx = ref_ri[ref_ri[i] : ref_ri[i + 1]]
        values = test_data[idx]
        h = histogram(values, minv=minv, maxv=maxv)
        hist = h["histogram"]
        pdf = hist / numpy.sum(hist)
        category_changes[category] = pdf * 100

    # split outputs into separate records
    result = dict()
    for category in FmaskCategories:
        fmt = "{}_2_{}"
        for category2 in FmaskCategories:
            key = fmt.format(category.name.lower(), category2.name.lower())
            result[key] = category_changes[category][category2.value]

    return result


def evaluate_categories(
    ref_ds: rasterio.io.DatasetReader,
    test_ds: rasterio.io.DatasetReader,
    categories: Union[FmaskRecords, ContiguityRecords, TerrainShadowRecords],
) -> Dict[str, float]:
    """
    A generic tool for evaluating categorical datasets.
    """
    values = [v.value for v in list(categories)]
    n_values = len(values)
    minv = min(values)
    maxv = max(values)

    # read data and reshape to 1D
    ref_data = ref_ds.read(1).ravel()
    test_data = test_ds.read(1).ravel()

    ref_h = histogram(ref_data, minv=minv, maxv=maxv, reverse_indices="ri")

    ref_hist = ref_h["histogram"]
    ref_ri = ref_h["ri"]

    category_changes = dict()

    for category in categories:
        i = category.value
        # check we have data for this category
        if ref_hist[i] == 0:
            # no changes as nothing exists in the reference data
            category_changes[category] = numpy.zeros((n_values,), dtype="int")
            continue
        idx = ref_ri[ref_ri[i] : ref_ri[i + 1]]
        values = test_data[idx]
        h = histogram(values, minv=minv, maxv=maxv)
        hist = h["histogram"]
        pdf = hist / numpy.sum(hist)
        category_changes[category] = pdf * 100

    # split outputs into separate records
    result = dict()
    for category in categories:
        fmt = "{}_2_{}"
        for category2 in categories:
            key = fmt.format(category.name.lower(), category2.name.lower())
            result[key] = category_changes[category][category2.value]

    return result


def data_mask(ds: rasterio.io.DatasetReader) -> numpy.ndarray:
    """Extract a mask of data and no data; handle a couple of cases."""
    nodata = ds.nodata
    if nodata is None:
        nodata = 0
    is_finite = numpy.isfinite(nodata)

    if is_finite:
        mask = ds.read(1) != nodata
    else:
        mask = numpy.isfinite(ds.read(1))

    return mask


def evaluate2(
    ref_ds: rasterio.io.DatasetReader, test_ds: rasterio.io.DatasetReader
) -> numpy.ndarray:
    """A basic difference operator where data exists at both index locations"""
    ref_mask = data_mask(ref_ds)
    test_mask = data_mask(test_ds)

    # evaluate only where valid data locations are the same
    mask = ref_mask & test_mask
    result = ref_ds.read(1)[mask] - test_ds.read(1)[mask]

    return result


def evaluate_nulls(
    ref_ds: rasterio.io.DatasetReader, test_ds: rasterio.io.DatasetReader
) -> Tuple[float, float]:
    """
    A basic eval for checking if null locations have changed.
    eg, data pixel to null pixel and vice versa.
    """
    nodata = ref_ds.nodata
    if nodata is None:
        nodata = 0
    is_finite = numpy.isfinite(nodata)

    mask = data_mask(ref_ds)

    # read data from both the data and nodata masks
    values = test_ds.read(1)[mask]
    values2 = test_ds.read(1)[~mask]

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
