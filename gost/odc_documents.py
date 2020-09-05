"""
Handles Open Data Cube metadata documents.
"""
import math
from pathlib import Path
from typing import Any, Dict, Optional, Union
import attr
import cattr
import numpy
import rasterio
import h5py
import yaml
import structlog

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
        d = attr.asdict(self)
        result = {"colour_{}".format(key): val for key, val in d.items()}

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

    abs_iterative_mean: AbsIterativeMean = None
    abs: Abs = None
    iterative_mean: IterativeMean = None
    iterative_stddev: IterativeStddev = None
    mean: Mean = None
    stddev: Stddev = None
    cep90: float = attr.ib(default=math.nan)

    def flatten(self):
        d = attr.asdict(self)
        result = {}
        for key in d:
            if isinstance(d[key], dict):
                for key2 in d[key]:
                    result["{}_{}".format(key, key2)] = d[key][key2]
            else:
                result[key] = d[key]

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
    residual: Residual = None
    fields: Dict[str, Any] = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        data = self.colors.flatten()
        data["final_qa_count"] = self.final_qa_count

        for key, value in self.residual.flatten().items():
            data[key] = value

        self.fields = data


@attr.s(auto_attribs=True)
class Measurement:
    """
    Refers to an individual measurement within an ODC document.
    """

    path: str
    parent_dir: str
    file_format: str
    band: Optional[int] = attr.ib()
    dataset_pathname: Optional[str] = None

    @band.default
    def band_default(self):
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

    def read(self) -> numpy.ndarray:
        """
        Basic method to read the data into memory.
        Can very easily be expanded to read subsets, resample etc.
        """

        pathname = self.pathname()
        if not pathname.exists():
            msg = "pathname not found"
            _LOG.info(msg, pathname=str(pathname))

            raise OSError(msg)

        # h5py is faster with I/O than reading HDF5 via GDAL
        if self.file_format == "HDF5":
            with h5py.File(str(pathname), "r") as fid:
                if self.dataset_pathname not in fid:
                    msg = "dataset pathname not found"
                    _LOG.info(
                        msg,
                        dataset_pathname=self.dataset_pathname,
                    )
                    raise KeyError(msg)

                data = fid[self.dataset_pathname][:]
        else:
            with rasterio.open(pathname, "r") as src:
                data = src.read(self.band)

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
    measurements: Dict[str, Measurement] = None


def _load_yaml_doc(path: Path) -> Dict:
    """Load a yaml document."""

    with open(path, "r") as src:
        doc = yaml.load(src, Loader=yaml.FullLoader)

    return doc


def load_odc_metadata(path: Path) -> Granule:
    """
    Load the ODC odc-metadata document.
    The checks for different old style metadata will be removed soon.

    :param path:
        Pathname to the *.odc-metadata.yaml document.

    :return:
        Granule class instance.
    """

    raw_doc = _load_yaml_doc(path)
    doc = {}

    if "product_type" in raw_doc:

        doc["product_name"] = raw_doc["product_type"]

        try:
            key = list(raw_doc["lineage"]["source_datasets"].keys())[0]
            # Sentinel-2 Collection-1
            doc["granule_id"] = raw_doc["lineage"]["source_datasets"][key]["tile_id"]
            doc["region_code"] = doc["granule_id"].split("_")[-2][1:]
            doc["framing"] = "MGRS"
            doc["parent_uuid"] = raw_doc["lineage"]["source_datasets"][key]["id"]
        except KeyError:
            # Landsat Collection-2
            l1_lineage = raw_doc["lineage"]["source_datasets"]["level1"]

            doc["granule_id"] = l1_lineage["usgs"]["scene_id"]

            xy = l1_lineage["image"]["satellite_ref_point_start"]
            path = xy["x"]
            row = xy["y"]
            doc["region_code"] = f"{path:03}{row:03}"
            doc["framing"] = "WRS2"
            doc["parent_uuid"] = l1_lineage["id"]

        measurements = raw_doc["image"]["bands"]
        doc["measurements"] = {key: {} for key in measurements}

        for meas in measurements:
            doc["measurements"][meas]["path"] = measurements[meas]["path"]
            doc["measurements"][meas]["file_format"] = "GeoTIFF"
            doc["measurements"][meas]["parent_dir"] = str(path.parent)
    else:
        # Landsat Collection-3
        doc["product_name"] = raw_doc["product"]["name"]
        doc["granule_id"] = raw_doc["properties"]["landsat:landsat_scene_id"]
        doc["region_code"] = raw_doc["properties"]["odc:region_code"]
        doc["measurements"] = raw_doc["measurements"]

        # assuming a single level-1 source
        doc["parent_uuid"] = raw_doc["lineage"]["level1"][0]

        file_format = raw_doc["properties"]["odc:file_format"]

        # file format is global in ODC; still it is better to define it per-measurement
        for measurement in doc["measurements"]:
            doc["measurements"][measurement]["file_format"] = file_format
            doc["measurements"][measurement]["parent_dir"] = str(path.parent)

    converter = cattr.Converter()
    granule = converter.structure(doc, Granule)

    return granule


def load_proc_info(path: Path) -> GeometricQuality:
    """
    Load the ODC proc-info metadata document.

    :param path:
        Pathname to the *.proc-info.yaml document.

    :return:
        GeometricQuality class instance.
    """

    doc = _load_yaml_doc(path)

    converter = cattr.Converter()
    gqa = converter.structure(doc["gqa"], GeometricQuality)

    return gqa


class ReadOdcMetadata:
    def __init__(self, pathname: str):
        with open(str(pathname)) as src:
            self._doc = yaml.load(src, Loader=yaml.FullLoader)

        if "product_type" in self._doc:
            self._eo3 = False
            key = list(self._doc["lineage"]["source_datasets"].keys())[0]
            self._product_name = self._doc["product_type"]
            try:
                # Sentinel-2 Collection-1
                self._granule = self._doc["lineage"]["source_datasets"][key]["tile_id"]
                # self._region_code = self._doc['lineage']['source_datasets'][key]['image']['tile_reference'][1:]
                self._region_code = self._granule.split("_")[-2][1:]
                self._framing = "MGRS"
            except KeyError:
                # Landsat Collection-2
                self._granule = self._doc["lineage"]["source_datasets"]["level1"][
                    "usgs"
                ]["scene_id"]
                xy = self._doc["lineage"]["source_datasets"]["level1"]["image"][
                    "satellite_ref_point_start"
                ]
                path = xy["x"]
                row = xy["y"]
                self._region_code = f"{path:03}{row:03}"

            self._measurements = self._doc["image"]["bands"]
        else:
            # Landsat Collection-3
            self._eo3 = True
            self._product_name = self._doc["product"]["name"]
            self._granule = self._doc["properties"]["landsat:landsat_scene_id"]
            self._region_code = self._doc["properties"]["odc:region_code"]
            self._measurements = self._doc["measurements"]
            self._parent_uuid = self._doc["lineage"]["level1"][
                0
            ]  # assuming a single level-1 source
            self._framing = "WRS2"

    @property
    def doc(self) -> Dict[str, Any]:
        return self._doc

    @property
    def eo3(self) -> bool:
        return self._eo3

    @property
    def product_name(self) -> str:
        return self._product_name

    @property
    def granule(self) -> str:
        return self._granule

    @property
    def region_code(self) -> str:
        return self._region_code

    @property
    def measurements(self) -> Dict[str, Any]:
        return self._measurements

    @property
    def parent_uuid(self) -> str:
        return self._parent_uuid

    @property
    def framing(self) -> str:
        return self._framing


class ReadOdcProcInfo:
    def __init__(self, pathname: str):
        with open(str(pathname)) as src:
            self._doc = yaml.load(src, Loader=yaml.FullLoader)

        self._pathname = pathname
        self._eo3 = True
        self._gqa = self._doc["gqa"]
        self._final_qa_count = {"final_qa_count": self._gqa["final_qa_count"]}

        self._handle_color_field()

        self._abs = {
            "abs_{}".format(key): value
            for key, value in self._gqa["residual"]["abs"].items()
        }
        self._abs_iterative_mean = {
            "abs_iterative_mean_{}".format(key): value
            for key, value in self._gqa["residual"]["abs_iterative_mean"].items()
        }
        self._iterative_mean = {
            "iterative_mean_{}".format(key): value
            for key, value in self._gqa["residual"]["iterative_mean"].items()
        }
        self._iterative_stddev = {
            "iterative_stddev_{}".format(key): value
            for key, value in self._gqa["residual"]["iterative_stddev"].items()
        }
        self._mean = {
            "mean_{}".format(key): value
            for key, value in self._gqa["residual"]["mean"].items()
        }
        self._stddev = {
            "stddev_{}".format(key): value
            for key, value in self._gqa["residual"]["stddev"].items()
        }
        self._cep90 = {"cep90": self._gqa["residual"]["cep90"]}

        self._fields = {}

        for prop in [
            self._final_qa_count,
            self._colors,
            self._abs,
            self._abs_iterative_mean,
            self._iterative_mean,
            self._iterative_stddev,
            self._mean,
            self._stddev,
            self._cep90,
        ]:
            for key, value in prop.items():
                self._fields[key] = value

    def _handle_color_field(self):
        """
        If GQA failed, then no color field is recorded. This is to prevent an
        error and still be able to process the record.
        """
        if "colors" not in self._gqa:
            _LOG.info(
                "no colors field in GQA info; inserting 0 as a replacement",
                gqa_error_message=self._gqa["error_message"],
                document_pathname=self._pathname,
            )
            self._colors = {
                "colors_{}".format(key): 0
                for key in [
                    "blue",
                    "green",
                    "red",
                    "teal",
                    "yellow",
                ]
            }
        else:
            self._colors = {
                "colors_{}".format(key): value
                for key, value in self._gqa["colors"].items()
            }

    @property
    def doc(self) -> Dict[str, Any]:
        return self._doc

    @property
    def pathname(self) -> str:
        return self._pathname

    @property
    def eo3(self) -> bool:
        return self._eo3

    @property
    def gqa(self) -> Dict[str, Any]:
        return self._gqa

    @property
    def colors(self) -> Dict[str, Any]:
        return self._colors

    @property
    def final_qa_count(self) -> int:
        return self._final_qa_count

    @property
    def abs(self) -> Dict[str, float]:
        return self._abs

    @property
    def abs_iterative_mean(self) -> Dict[str, float]:
        return self._abs_iterative_mean

    @property
    def iterative_mean(self) -> Dict[str, float]:
        return self._iterative_mean

    @property
    def iterative_stddev(self) -> Dict[str, float]:
        return self._iterative_stddev

    @property
    def mean(self) -> Dict[str, float]:
        return self._mean

    @property
    def stddev(self) -> Dict[str, float]:
        return self._stddev

    @property
    def cep90(self) -> float:
        return self._cep90

    @property
    def fields(self) -> Dict[str, Any]:
        return self._fields
