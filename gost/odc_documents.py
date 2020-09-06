"""
Handles Open Data Cube metadata documents.
"""
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from affine import Affine  # type: ignore
import attr
import cattr
import numpy  # type: ignore
import rasterio  # type: ignore
import h5py  # type: ignore
import yaml
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

    abs_iterative_mean: Union[AbsIterativeMean, None] = None
    abs: Union[Abs, None] = None
    iterative_mean: Union[IterativeMean, None] = None
    iterative_stddev: Union[IterativeStddev, None] = None
    mean: Union[Mean, None] = None
    stddev: Union[Stddev, None] = None
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
    residual: Union[Residual, None] = None
    fields: Dict[str, Any] = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self):
        data = self.colors.flatten()
        data["final_qa_count"] = self.final_qa_count

        for key, value in self.residual.flatten().items():
            data[key] = value

        self.fields = data


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
    """

    path: str
    parent_dir: str
    file_format: str
    band: Optional[int] = attr.ib()
    dataset_pathname: Optional[str] = None
    transform: List = attr.ib(converter=_convert_transform, default=None)
    shape: Union[Tuple[int, int], None] = attr.ib(converter=tuple, default=None)

    @band.default
    def band_default(self):
        # no need to have a band index number with HDF5
        if self.file_format == "HDF5":
            value = None
        else:
            value = 1

        return value

    # def __attrs_post_init__(self):
    #     """
    #     Initialise some attributes post init.
    #     Unfortunately we have to do a file open to get the
    #     nodata value.
    #     In order to return without failure, None is returned for those
    #     cases where the file can't be opened.
    #     The transform, and shape attributes could also be initialied
    #     here instead of passing them through.
    #     """
    #     if self.inspect_measurement:
    #         pathname = self.pathname()
    #         if not pathname.exists():
    #             msg = "pathname not found, setting nodata to None"
    #             _LOG.info(msg, pathname=str(pathname))

    #             self.nodata = None
    #         else:
    #             if self.file_format == "HDF5":
    #                 with h5py.File(str(pathname), "r") as fid:
    #                     if self.dataset_pathname not in fid:
    #                         msg = "dataset pathname not found"
    #                         _LOG.info(
    #                             msg,
    #                             dataset_pathname=self.dataset_pathname,
    #                         )
    #                         raise KeyError(msg)

    #                     ds = fid[self.dataset_pathname]
    #                     nodata = ds.attrs.get("no_data_value", None)
    #                     if nodata is None:
    #                         nodata = ds.fillvalue
    #             else:
    #                 with rasterio.open(pathname) as src:
    #                     nodata = src.nodata

    #             self.nodata = nodata
    #     else:
    #         self.nodata = None

    def pathname(self) -> Path:
        """Return full pathname to the file."""

        pathname = Path(self.parent_dir, self.path)

        return pathname

    def nodata(self):
        """Retrieve the nodata value."""

        pathname = self.pathname()
        if not pathname.exists():
            msg = "pathname not found, setting nodata to None"
            _LOG.info(msg, pathname=str(pathname))

            no_data = None
        else:
            if self.file_format == "HDF5":
                with h5py.File(str(pathname), "r") as fid:
                    if self.dataset_pathname not in fid:
                        msg = "dataset pathname not found"
                        _LOG.info(
                            msg,
                            dataset_pathname=self.dataset_pathname,
                        )
                        raise KeyError(msg)

                    ds = fid[self.dataset_pathname]
                    no_data = ds.attrs.get("no_data_value", None)
                    if no_data is None:
                        no_data = ds.fillvalue
            else:
                with rasterio.open(pathname) as src:
                    no_data = src.nodata

        return no_data

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
    measurements: Union[Dict[str, Measurement], None] = None
    proc_info: str = attr.ib(default="")


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
            doc["measurements"][meas]["transform"] = measurements[meas]["info"]["geotransform"]
            doc["measurements"][meas]["shape"] = [
                measurements[meas]["info"]["height"],
                measurements[meas]["info"]["width"],
            ]
    else:
        # Landsat Collection-3
        doc["product_name"] = raw_doc["product"]["name"]
        doc["granule_id"] = raw_doc["properties"]["landsat:landsat_scene_id"]
        doc["region_code"] = raw_doc["properties"]["odc:region_code"]
        doc["measurements"] = raw_doc["measurements"]
        doc["framing"] = "WRS2"

        # assuming a single level-1 source
        doc["parent_uuid"] = raw_doc["lineage"]["level1"][0]

        file_format = raw_doc["properties"]["odc:file_format"]

        grids = raw_doc["grids"]

        doc["proc_info"] = raw_doc["accessories"]["metadata:processor"]["path"]

        # file format is global in ODC; still it is better to define it per-measurement
        for measurement in doc["measurements"]:
            doc["measurements"][measurement]["file_format"] = file_format
            doc["measurements"][measurement]["parent_dir"] = str(path.parent)

            # shape and transform
            grid = doc["measurements"][measurement].get("grid", "default")
            for key, value in grids[grid].items():
                doc["measurements"][measurement][key] = value

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
