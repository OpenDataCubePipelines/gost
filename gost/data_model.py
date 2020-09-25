"""
Contains the constructs for defining the data model when deserialising
the yaml documents, and forms the basis of the intercomparison workflow.
"""
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import attr
from affine import Affine  # type: ignore
import numpy  # type: ignore
import rasterio  # type: ignore
import structlog  # type: ignore

_LOG = structlog.get_logger()


@attr.s()
class GqaColours:
    """
    Colours section of the GQA report. Refers to a histogram count of
    GCP's.
    """

    blue: int = attr.ib(default=0)
    green: int = attr.ib(default=0)
    red: int = attr.ib(default=0)
    teal: int = attr.ib(default=0)
    yellow: int = attr.ib(default=0)

    def flatten(self):
        """Flatten the class attributes into a dict."""

        converted = attr.asdict(self)
        result = {f"colour_{key}": val for key, val in converted.items()}

        return result


@attr.s()
class AbsIterativeMean:
    """
    Geometric quality: Absolute value iterative mean.
    """

    x: float = attr.ib(default=math.nan)
    y: float = attr.ib(default=math.nan)
    xy: float = attr.ib(default=math.nan)


@attr.s()
class Abs:
    """
    Geometric quality: Absolute value.
    """

    x: float = attr.ib(default=math.nan)
    y: float = attr.ib(default=math.nan)
    xy: float = attr.ib(default=math.nan)


@attr.s()
class IterativeMean:
    """
    Geometric quality: Iterative mean.
    """

    x: float = attr.ib(default=math.nan)
    y: float = attr.ib(default=math.nan)
    xy: float = attr.ib(default=math.nan)


@attr.s()
class IterativeStddev:
    """
    Geometric quality: Iterative standard deviation.
    """

    x: float = attr.ib(default=math.nan)
    y: float = attr.ib(default=math.nan)
    xy: float = attr.ib(default=math.nan)


@attr.s()
class Mean:
    """
    Geometric quality: Mean.
    """

    x: float = attr.ib(default=math.nan)
    y: float = attr.ib(default=math.nan)
    xy: float = attr.ib(default=math.nan)


@attr.s()
class Stddev:
    """
    Geometric quality: Standard deviation.
    """

    x: float = attr.ib(default=math.nan)
    y: float = attr.ib(default=math.nan)
    xy: float = attr.ib(default=math.nan)


@attr.s()
class Cep90:
    """
    Geometric quality: Circular Error Probable 90%.
    """

    cep90: float = attr.ib(default=math.nan)


@attr.s(auto_attribs=True)
class Residual:
    """
    Ground Control Point residual analysis section of the geometric
    quality metadata.
    """

    abs_iterative_mean: Union[AbsIterativeMean, None] = None
    abs: Union[Abs, None] = None
    iterative_mean: Union[IterativeMean, None] = None
    iterative_stddev: Union[IterativeStddev, None] = None
    mean: Union[Mean, None] = None
    stddev: Union[Stddev, None] = None
    cep90: float = attr.ib(default=math.nan)

    def flatten(self):
        """Flatten the class attributes into a dict."""

        converted = attr.asdict(self)
        result = {}
        for key in converted:
            if isinstance(converted[key], dict):
                for key2 in converted[key]:
                    result[f"{key}_{key2}"] = converted[key][key2]
            else:
                result[key] = converted[key]

        return result


@attr.s(auto_attribs=True)
class GeometricQuality:
    """
    Geometric Quality metadata of the proc-info metadata document.
    Note: colors is intentially spelt the US way.
    """

    colors: GqaColours = attr.ib(default=GqaColours())
    error_message: str = attr.ib(default="")
    final_qa_count: int = attr.ib(default=0)
    granule: str = attr.ib(default="")
    ref_date: str = attr.ib(default="")
    ref_source: str = attr.ib(default="")
    ref_source_path: str = attr.ib(default="")
    residual: Union[Residual, None] = None
    fields: Dict[str, Any] = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        data = self.colors.flatten()
        data["final_qa_count"] = self.final_qa_count

        for key, value in self.residual.flatten().items():
            data[key] = value

        self.fields = data


@attr.s(auto_attribs=True)
class Brdf:
    """
    Refers to the Alpha-1 and Alpha-2 BRDF components for a given band.
    """

    alpha_1: Union[Dict[str, float], None] = None
    alpha_2: Union[Dict[str, float], None] = None
    id: Union[List[Any], None] = None
    tier: Union[str, None] = None

    def flatten(self):
        """Flatten the class attributes into a dict."""

        skip = ["id", "tier"]
        data = attr.asdict(self, filter=lambda attr, value: attr.name not in skip)

        result = {}

        for key, value in data.items():
            for key2, value2 in value.items():
                result[f"{key}_{key2}"] = value2

        return result


@attr.s(auto_attribs=True)
class Aerosol:
    """
    Contains the information relating to the aerosol component used
    within the processing pipeline.
    """

    value: Union[float, None] = None
    id: Union[List[Any], None] = None
    tier: Union[str, None] = None


@attr.s(auto_attribs=True)
class Ozone:
    """
    Contains the information relating to the ozone component used
    within the processing pipeline.
    """

    value: Union[float, None] = None
    id: Union[List[Any], None] = None
    tier: Union[str, None] = None


@attr.s(auto_attribs=True)
class WaterVapour:
    """
    Contains the information relating to the water vapour component used
    within the processing pipeline.
    """

    value: Union[float, None] = None
    id: Union[List[Any], None] = None
    tier: Union[str, None] = None


@attr.s(auto_attribs=True)
class AncillaryInfo:
    """
    Ancillary value information of the proc-info metadata document.
    """

    aerosol: Union[Aerosol, None] = None
    brdf: Union[Brdf, None] = None
    ozone: Union[Ozone, None] = None
    water_vapour: Union[WaterVapour, None] = None

    def flatten(self) -> Dict[str, Any]:
        """
        Converts the class attributes and their values to a dict.
        """
        skip = ["id", "tier", "brdf"]
        data = attr.asdict(self, filter=lambda attr, value: attr.name not in skip)

        result = self.brdf.flatten()

        for key, value in data.items():
            result[key] = value["value"]

        return result


@attr.s(auto_attribs=True)
class SoftwareVersion:
    """
    Software version information from the proc-info metadata document.
    """

    name: Union[str, None] = None
    url: Union[str, None] = None
    version: Union[str, None] = None


@attr.s(auto_attribs=True)
class GranuleProcInfo:
    """
    Basic class containing information pertaining to the processing
    info for a given granule.
    """

    geometric_quality: Union[GeometricQuality, None] = None
    ancillary: Union[AncillaryInfo, None] = None
    software_versions: Union[Dict[str, SoftwareVersion], None] = None


def _convert_transform(transform: List[Any]) -> Affine:
    """Create Affine transform."""

    if len(transform) == 9:
        affine_transform = Affine(*transform[:-3])
    else:
        affine_transform = Affine(*transform)

    return affine_transform


@attr.s(auto_attribs=True)
class Measurement:
    """
    Refers to an individual measurement within an ODC document.

    Attributes:
    ----------

    :path:
        Name of the file.
    :parent_dir:
        Name of the parent directory the file resides in.
    :file_format:
        E.g. GeoTIFF, HDF5 etc.
    :band:
        Integer band index (1, n).
    :dataset_pathname:
        For container files like HDF5, the pathname to the dataset
        within the file.
    :transform:
        Affine transformation.
    :shape:
        Shape in (height, width) of the dataset.
    :nodata:
        The no data value of the dataset.
    :closed:
        Is the file and/or dataset openeded.
    :dataset:
        Data access layer.
    """

    # TODO: HDF5 measurement class to simplify IO on measurements
    # within the same file. Required for upcoming sensitivity analysis.
    path: str
    parent_dir: str
    file_format: str
    band: Optional[int] = attr.ib()
    dataset_pathname: Optional[str] = None
    transform: List = attr.ib(converter=_convert_transform, default=None)
    shape: Union[Tuple[int, int], None] = attr.ib(converter=tuple, default=None)
    nodata: Any = None
    closed: bool = True
    dataset: Any = None

    @band.default
    def band_default(self):
        """Set the default band id number."""

        # no need to have a band index number with HDF5
        if self.file_format == "HDF5":
            value = None
        else:
            value = 1

        return value

    def pathname(self) -> Path:
        """Return full pathname to the file."""

        pathname = Path(self.parent_dir, self.path)

        return pathname

    def open(self):
        """Open the dataset."""

        pathname = self.pathname()
        if not pathname.exists():
            msg = "pathname not found"
            _LOG.info(msg, pathname=str(pathname))

            raise OSError(msg)

        self.dataset = rasterio.open(pathname)
        self.nodata = self.dataset.nodata
        self.closed = False

    def close(self):
        """Close the dataset."""

        self.dataset.close()
        self.closed = True

    def read(self) -> numpy.ndarray:
        """
        Basic method to read the data into memory.
        Can very easily be expanded to read subsets, resample etc.
        """

        data = self.dataset.read(self.band)

        return data


@attr.s(auto_attribs=True)
class Granule:
    """
    Basic class containing information pertaining to the granule.
    """

    granule_id: str = attr.ib(default="")
    region_code: str = attr.ib(default="")
    product_name: str = attr.ib(default="")
    parent_uuid: str = attr.ib(default="")
    framing: str = attr.ib(default="")
    measurements: Union[Dict[str, Measurement], None] = None
    proc_info: str = attr.ib(default="")
