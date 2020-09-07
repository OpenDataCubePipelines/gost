"""
Utils pertaining to the creation of the PNG plots.
"""
from pathlib import Path
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.colors as colors  # type: ignore
import geopandas  # type: ignore
import structlog  # type: ignore
import zstandard  # type: ignore

from gost.constants import TM_WORLD_BORDERS_FNAME

COLOURMAP = "rainbow"
REFLECTANCE_MAPPING = [
    (
        "min_residual",
        "% Reflectance",
        "rainbow_r",
    ),  # reverse so red indicates greater change
    ("max_residual", "% Reflectance", COLOURMAP),
    ("percentile_90", "% Reflectance", COLOURMAP),
    ("percentile_99", "% Reflectance", COLOURMAP),
    ("percent_different", "% of Pixels where residiual != 0", COLOURMAP),
    ("mean_residual", "% Reflectance", COLOURMAP),
    ("standard_deviation", "% Reflectance", COLOURMAP),
    ("skewness", "Skewness", COLOURMAP),
    ("kurtosis", "Kurtosis", COLOURMAP),
]
OA_COLUMNS = [
    "min_residual",
    "max_residual",
    "percentile_90",
    "percentile_99",
    "percent_different",
    "mean_residual",
    "standard_deviation",
    "skewness",
    "kurtosis",
]
_LOG = structlog.get_logger()


# TODO: Needs an overhaul so it is less duplicative
def _plot_reflectance_stats(
    gdf_subset: geopandas.GeoDataFrame,
    tm_gdf: geopandas.GeoDataFrame,
    name: str,
    outdir: Path,
) -> None:
    """Plotting func specifically for the reflectance datasets."""

    for column, label, colourmap in REFLECTANCE_MAPPING:

        prefix = Path(outdir, name.split("_")[0])
        if not prefix.exists():
            _LOG.info("creating output directory", outdir=str(prefix))
            prefix.mkdir(parents=True)

        out_fname = prefix.joinpath("{}-{}.png".format(name, column))

        fig = plt.figure(figsize=(3, 3))
        axes = fig.add_subplot()

        norm = colors.Normalize(
            vmin=gdf_subset[column].min(), vmax=gdf_subset[column].max()
        )
        colourbar = plt.cm.ScalarMappable(norm=norm, cmap=colourmap)

        ax_cbar = fig.colorbar(colourbar, ax=axes)
        ax_cbar.set_label(label)

        gdf_subset.plot(column=column, cmap=colourmap, legend=False, ax=axes)

        tm_gdf.plot(linewidth=0.25, edgecolor="black", facecolor="none", ax=axes)

        axes.set_xlim(105, 160)
        axes.set_ylim(-45, -5)
        axes.set_xlabel("longitude")
        axes.set_ylabel("latitude")

        _LOG.info("saving figure as png", out_fname=str(out_fname))

        plt.savefig(out_fname, bbox_inches="tight")
        plt.close(fig)


def _plot_oa_stats(
    gdf_subset: geopandas.GeoDataFrame,
    tm_gdf: geopandas.GeoDataFrame,
    name: str,
    outdir: Path,
) -> None:
    """Plotting func specifically for the observation attribute datasets."""

    labels = {
        "oa_time_delta": "Seconds",
        "oa_relative_slope": "Slope",
    }
    other_labels = {
        "kurtosis": "Kurtosis",
        "skewness": "Skewness",
    }

    label = labels.get(name, "Degrees")

    for column in OA_COLUMNS:
        prefix = Path(outdir, name.split("_")[0])
        if not prefix.exists():
            _LOG.info("creating output directory", outdir=str(prefix))
            prefix.mkdir(parents=True)

        label = other_labels.get(label, label)

        out_fname = prefix.joinpath("{}-{}.png".format(name, column))

        fig = plt.figure(figsize=(3, 3))
        axes = fig.add_subplot()

        norm = colors.Normalize(
            vmin=gdf_subset[column].min(), vmax=gdf_subset[column].max()
        )
        colourbar = plt.cm.ScalarMappable(norm=norm, cmap=COLOURMAP)

        ax_cbar = fig.colorbar(colourbar, ax=axes)
        ax_cbar.set_label(label)

        gdf_subset.plot(column=column, cmap=COLOURMAP, legend=False, ax=axes)

        tm_gdf.plot(linewidth=0.25, edgecolor="black", facecolor="none", ax=axes)

        axes.set_xlim(105, 160)
        axes.set_ylim(-45, -5)
        axes.set_xlabel("longitude")
        axes.set_ylabel("latitude")

        _LOG.info("saving figure as png", out_fname=str(out_fname))

        plt.savefig(out_fname, bbox_inches="tight")
        plt.close(fig)


def plot_pngs(gdf: geopandas.GeoDataFrame, outdir: Path) -> None:
    """
    General plotting routine of the residuals analysis.
    Currently only interested in the surface reflectance measurements,
    but can easily be expanded to to incorporate other measurements.
    """

    _LOG.info("reading the TM WORLD BORDERS dataset")

    with open(TM_WORLD_BORDERS_FNAME, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        tm_gdf = geopandas.read_file(dctx.stream_reader(src))

    for name, grp in gdf.groupby("measurement"):

        if "nbar" in name:
            _plot_reflectance_stats(grp, tm_gdf, name, outdir)
        else:
            _plot_oa_stats(grp, tm_gdf, name, outdir)

    _LOG.info("finished producing plots")
