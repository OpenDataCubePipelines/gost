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

from pathlib import Path
from typing import Any, Dict, Tuple
import pandas  # type: ignore
import geopandas  # type: ignore
import structlog  # type: ignore
import zstandard  # type: ignore

from gost.constants import SUMMARISE_FUNCS, FRAMING

_LOG = structlog.get_logger()


def merge_framing(dataframe: pandas.DataFrame, framing: str) -> geopandas.GeoDataFrame:
    """
    Output files will be created as GeoJSONSeq (JSONLines).
    As such, a filename extension of .geojsonl should be used.
    """

    framing_pathname = FRAMING[framing]

    _LOG.info("loading framing geometry")

    # read required framing geometry
    with open(framing_pathname, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        framing_dataframe = geopandas.read_file(dctx.stream_reader(src))

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


def summarise(
    geo_dataframe: geopandas.GeoDataFrame,
    thematic: bool,
    proc_info: bool,
) -> pandas.DataFrame:
    """
    Produce summary statistics for the generic and thematic datasets.
    Essentially this is a global summary. i.e. for each measurement
    across the entire spatial extent, what is the min, max and mean
    value for each statistical measure.
    """

    if proc_info:
        _LOG.info("summarising proc info data")
        skip = [
            "reference_pathname",
            "test_pathname",
            "region_code",
            "granule_id",
            "geometry",
        ]
        cols = [i for i in geo_dataframe.columns if i not in skip]

        subset = geo_dataframe[cols]

        result = pandas.DataFrame()
        result["minv"] = subset.min(axis=0)
        result["maxv"] = subset.max(axis=0)
    else:
        if thematic:
            _LOG.info("summarising thematic datasets")
            cols = [i for i in geo_dataframe.columns if "_2_" in i]
        else:
            _LOG.info("summarising generic datasets")
            cols = ["min_residual", "max_residual", "percent_different"]

        result = pandas.pivot_table(
            geo_dataframe, index=["measurement"], values=cols, aggfunc=SUMMARISE_FUNCS
        )

        # we're reshaping here simply to get a cleaner table structure to output
        result = result.transpose().unstack().transpose()

    return result


def global_min_max(dataframe: pandas.DataFrame) -> pandas.DataFrame:
    """Return min/max global summary."""
    columns = [i for i in dataframe.index.get_level_values(0) if "nbar" in i]

    result = dataframe.loc[(columns, ["max_residual", "min_residual"]), :]

    return result


def reflectance_pass_fail(
    dataframe: pandas.DataFrame,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Evaluate a final pass/fail result for the reflectance products."""

    def test(dataframe: pandas.DataFrame, nbar: bool) -> Dict[str, Any]:
        cols = [i for i in dataframe.index.get_level_values(0) if "nbar" in i]

        if nbar:
            columns = [col for col in cols if "nbart" not in col]
        else:
            columns = [col for col in cols if "nbart" in col]

        subset = dataframe.loc[(columns, ["max_residual", "min_residual"]), :]

        minv = subset.min(axis=0)["amin"]
        maxv = subset.max(axis=0)["amax"]

        test_passed = max(abs(minv), abs(maxv)) <= 1

        result = {"minv": minv, "maxv": maxv, "test_passed": test_passed}

        return result

    nbar_result = test(dataframe, True)

    _LOG.info(
        "final reflectance evaluation",
        product="NBAR",
        test_passed=nbar_result["test_passed"],
        min_residual=nbar_result["minv"],
        max_residual=nbar_result["maxv"],
    )

    nbart_result = test(dataframe, True)

    _LOG.info(
        "final reflectance evaluation",
        product="NBART",
        test_passed=nbart_result["test_passed"],
        min_residual=nbart_result["minv"],
        max_residual=nbart_result["maxv"],
    )

    return nbar_result, nbart_result


def create_general_csvs(dataframe: pandas.DataFrame, outdir: Path) -> None:
    """Produce CSV's of the general intercomparison results."""

    measurements = dataframe.index.get_level_values(0).unique()
    reflectance_keep = [col for col in measurements if "nbar" in col]
    nbar_keep = [col for col in reflectance_keep if "nbart" not in col]
    nbart_keep = [col for col in reflectance_keep if "nbart" in col]
    oa_keep = [col for col in measurements if "oa_" in col]

    col_groups = {
        "nbar": nbar_keep,
        "nbart": nbart_keep,
        "oa": oa_keep,
    }

    for name, group in dataframe.groupby(level=1):
        drop1 = group.droplevel(1)

        if "min" in name:
            for product_group in col_groups:
                subset = drop1.loc[(col_groups[product_group])]

                subset_drop = (
                    subset.drop(columns=["amax", "mean"])
                    .reset_index()
                    .rename(columns={"amin": "Minimum", "measurement": "Measurement"})
                )

                out_fname = str(outdir.joinpath(f"{product_group}_{name}.csv"))

                _LOG.info("writing csv", out_fname=out_fname)
                subset_drop.to_csv(out_fname, index=False)
        else:
            for product_group in col_groups:
                subset = drop1.loc[(col_groups[product_group])]

                subset_drop = (
                    subset.drop(columns=["amin", "mean"])
                    .reset_index()
                    .rename(columns={"amax": "Maximum", "measurement": "Measurement"})
                )

                out_fname = str(outdir.joinpath(f"{product_group}_{name}.csv"))

                _LOG.info("writing csv", out_fname=out_fname)
                subset_drop.to_csv(out_fname, index=False)
