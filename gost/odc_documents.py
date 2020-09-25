"""
Handles the deserialisation of Open Data Cube metadata documents.
"""
from pathlib import Path
from typing import Dict
import cattr
import yaml
import structlog  # type: ignore

from gost.data_model import Granule, GranuleProcInfo

_LOG = structlog.get_logger()


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
            doc["measurements"][meas]["transform"] = measurements[meas]["info"][
                "geotransform"
            ]
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


def load_proc_info(path: Path) -> GranuleProcInfo:
    """
    Load the ODC proc-info metadata document.

    :param path:
        Pathname to the *.proc-info.yaml document.

    :return:
        GeometricQuality class instance.
    """

    doc = _load_yaml_doc(path)

    software = {i["name"]: i for i in doc["software_versions"]}

    sections = {
        "geometric_quality": doc["gqa"],
        "ancillary": doc["wagl"]["ancillary"],
        "software_versions": software,
    }

    converter = cattr.Converter()
    # gqa = converter.structure(doc["gqa"], GeometricQuality)

    processing_info = converter.structure(sections, GranuleProcInfo)

    return processing_info
