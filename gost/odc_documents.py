import yaml
import structlog
from typing import Any, Dict

_LOG = structlog.get_logger()


class Digestyaml:
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


class DigestProcInfo:
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
