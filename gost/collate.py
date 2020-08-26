"""
The collate module serves two primary purposes, merging and summarising.

Merging enables the results to be plotted in a spatial context in order
to more easily identify particular spatial patterns and distributions.
i.e. We merge the results of the intercomparison with framing geometry
of the product e.g. Sentinel-2 MGRS tiles, Landsat WRS2 Path/Row.

Summarising in this context means evaluating a global summary statistic
(collapsing all statistical results from a spatial context to a single
value).  The summary statistical measures are simply:

* min
* max
* mean

For example, the minimum difference of the blue channel, will be
summarised to determine the minimum, mean, and maximum value.
The basic idea is to get a measure of the spread for each statistical
result for each measurement.
"""

import pandas
import geopandas
import structlog
import zstandard

from gost.constants import SUMMARISE_FUNCS, FRAMING

_LOG = structlog.get_logger()


def merge_framing(dataframe, framing):
    """
    Output files will be created as GeoJSONSeq (JSONLines).
    As such, a filename extension of .geojsonl should be used.
    """

    framing_pathname = FRAMING[framing]

    _LOG.info("loading framing geometry")

    # read required framing geometry
    with open(framing_pathname, "rb") as src:
        cctx = zstandard.ZstdDecompressor()
        framing_dataframe = geopandas.read_file(cctx.stream_reader(src))

    _LOG.info("merging intercomparison results with framing geometry")

    # table merge based on region code
    new_df = pandas.merge(
        dataframe,
        framing_dataframe,
        how="left",
        left_on=["region_code"],
        right_on=["region_code"],
    )

    # save geojson
    gdf = geopandas.GeoDataFrame(new_df, crs=framing_dataframe.crs)

    return gdf


def summarise(geo_dataframe, categorical):
    """
    Produce summary statistics for the generic and categorical datasets.
    Essentially this is a global summary. i.e. for each measurement
    across the entire spatial extent, what is the min, max and mean
    value for each statistical measure.
    """

    if categorical:
        _LOG.info("summarising categorical datasets")
        cols = [i for i in geo_dataframe.columns if "_2_" in i]
    else:
        _LOG.info("summarising generic datasets")
        cols = ["minv", "maxv", "percent_different"]

    pivot = pandas.pivot_table(
        geo_dataframe, index=["measurement"], values=cols, aggfunc=SUMMARISE_FUNCS
    )

    # we're reshaping here simply to get a cleaner table structure to output
    pivot = pivot.transpose().unstack().transpose()

    return pivot
