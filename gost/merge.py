"""
Merge the results of the intercomparison with framing geometry of the
product e.g. Sentinel-2 MGRS tiles, Landsat WRS2 Path/Row.
This enables the results to be plotted in a spatial context in order
to more easily identify particular spatial patterns and distributions.
"""

from pathlib import Path
import pkg_resources
import h5py
import pandas
import geopandas
import zstandard

from wagl.hdf5 import read_h5_table

WRS2_FNAME = pkg_resources.resource_filename(
    "gost", "data/landsat_wrs2_descending.geojsonl.zstd"
)
MGRS_FNAME = pkg_resources.resource_filename(
    "gost", "data/sentinel-2-mgrs.geojsonl.zstd"
)
FRAMING = {
    "WRS2": WRS2_FNAME,
    "MGRS": MGRS_FNAME,
}


# TODO; it might be better to pass in the data, and return data.
#       rather than the do the IO component.
def merge_framing(pathname, out_pathname, framing, dataset_name):
    """
    Output files will be created as GeoJSONSeq (JSONLines).
    As such, a filename extension of .geojsonl should be used.
    """

    pathname = Path(pathname)
    out_pathname = Path(out_pathname)
    framing_pathname = FRAMING[framing]

    if not out_pathname.parent.exists():
        out_pathname.parent.mkdir()

    # read each table
    with h5py.File(str(pathname), "r") as fid:
        df = read_h5_table(fid, dataset_name)

    # read required framing geometry
    with open(framing_pathname, "rb") as src:
        cctx = zstandard.ZstdDecompressor()
        framing_df = geopandas.read_file(cctx.stream_reader(src))

    # table merge based on region code
    new_df = pandas.merge(
        df, framing_df, how="left", left_on=["region_code"], right_on=["region_code"]
    )

    # save geojson
    gdf = geopandas.GeoDataFrame(new_df, crs=framing_df.crs)
    gdf.to_file(str(out_pathname), driver="GeoJSONSeq")
