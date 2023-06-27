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
            doc["granule_id"] = raw_doc["tile_id"]
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
        key_map_dict = {'exiting':'oa_exiting_angle', 
            'fmask':'oa_fmask', 
            'incident':'oa_incident_angle', 
            'nbart_contiguity':'oa_nbart_contiguity', 
            'relative_azimuth':'oa_relative_azimuth', 
            'relative_slope':'oa_relative_slope', 
            'satellite_azimuth':'oa_satellite_azimuth', 
            'satellite_view':'oa_satellite_view', 
            'solar_azimuth':'oa_solar_azimuth', 
            'solar_zenith':'oa_solar_zenith', 
            'timedelta':'oa_time_delta',
            'azimuthal_exiting': 'oa_azimuthal_exiting',
            'azimuthal_incident': 'oa_azimuthal_incident',
            'terrain_shadow': 'oa_combined_terrain_shadow'
            }

        doc["measurements"] = {(key_map_dict[k] if k in key_map_dict else k):v  for (k,v) in doc["measurements"].items()}

    elif raw_doc["product"]["name"] == "ga_s2am_ard_3" or raw_doc["product"]["name"] == "ga_s2bm_ard_3":
        # Sentinel Collection-3
        doc["product_name"] = raw_doc["product"]["name"]
        doc["granule_id"] = raw_doc["properties"]["sentinel:sentinel_tile_id"]
        doc["region_code"] = raw_doc["properties"]["odc:region_code"]
        doc["measurements"] = raw_doc["measurements"]
        doc["framing"] = "MGRS"
 
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

    if "product_type" in doc:

        software = {}

        for i in doc["software_versions"]:
            software["name"] = i
            software.update(doc["software_versions"].get(i))

        software = {i["name"]: i for i in [software]}

        doc["wagl"] = {
            "ancillary": {
                "aerosol":{
                    "id":[
                        ""
                    ],
                    "tier":"",
                    "value": doc["lineage"]["ancillary"]["aerosol"]["value"]
                },
                "brdf":{
                    "alpha_1":{
                        "band_2": doc["lineage"]["ancillary"]["brdf_vol_band_2"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_2"]["value"],
                        "band_3": doc["lineage"]["ancillary"]["brdf_vol_band_3"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_3"]["value"],
                        "band_4": doc["lineage"]["ancillary"]["brdf_vol_band_4"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_4"]["value"],
                        "band_8": doc["lineage"]["ancillary"]["brdf_vol_band_8"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_8"]["value"],
                    },
                    "alpha_2":{
                        "band_2": doc["lineage"]["ancillary"]["brdf_geo_band_2"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_2"]["value"],
                        "band_3": doc["lineage"]["ancillary"]["brdf_geo_band_3"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_3"]["value"],
                        "band_4": doc["lineage"]["ancillary"]["brdf_geo_band_4"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_4"]["value"],
                        "band_8": doc["lineage"]["ancillary"]["brdf_geo_band_8"]["value"]/doc["lineage"]["ancillary"]["brdf_iso_band_8"]["value"],
                },
                    "id":[
                        ""
                    ],
                    "tier": ""
                },
                "elevation":{
                    "id":[
                        ""
                    ]
                },
                "ozone":{
                    "id":[
                        ""
                    ],
                    "tier": "",
                    "value": doc["lineage"]["ancillary"]["ozone"]["value"]
                },
                "water_vapour":{
                    "id":[
                         ""
                    ],
                    "tier": "",
                    "value": doc["lineage"]["ancillary"]["water_vapour"]["value"]
                }
            }
        }

    else:
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
