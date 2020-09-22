"""
Utils pertaining to the creation of the PNG plots.

Useful links:

* https://moonbooks.org/Articles/How-to-match-the-colorbar-size-with-the-figure-size-in-matpltolib-/
* https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
* https://matplotlib.org/3.1.0/gallery/axes_grid1/demo_colorbar_with_inset_locator.html
* https://stackoverflow.com/questions/40705614/hide-axis-label-only-not-entire-axis-in-pandas-plot
* https://github.com/geopandas/geopandas/issues/318
"""
from collections import namedtuple
from pathlib import Path
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.colors as colors  # type: ignore
from mpl_toolkits.axes_grid1 import make_axes_locatable  # type: ignore
import geopandas  # type: ignore
import structlog  # type: ignore
import zstandard  # type: ignore

from gost.constants import TM_WORLD_BORDERS_FNAME

COLORMAP = "rainbow"
REFLECTANCE_LABEL = "% Reflectance"
DEGREES_LABEL = "Degrees"
PlotInfo = namedtuple("PlotInfo", ["column", "label", "colormap"])
PlotInfoOa = namedtuple("PlotInfoOa", ["column", "colormap"])

REFLECTANCE_INFO = [
    PlotInfo(column="min_residual", label=REFLECTANCE_LABEL, colormap="rainbow_r"),
    PlotInfo(column="max_residual", label=REFLECTANCE_LABEL, colormap=COLORMAP),
    PlotInfo(column="percentile_90", label=REFLECTANCE_LABEL, colormap=COLORMAP),
    PlotInfo(column="percentile_99", label=REFLECTANCE_LABEL, colormap=COLORMAP),
    PlotInfo(
        column="percent_different",
        label="% of Pixels where residiual != 0",
        colormap=COLORMAP,
    ),
    PlotInfo(column="mean_residual", label=REFLECTANCE_LABEL, colormap="gist_rainbow"),
    PlotInfo(column="standard_deviation", label=REFLECTANCE_LABEL, colormap=COLORMAP),
    PlotInfo(column="skewness", label="Skewness", colormap="gist_rainbow"),
    PlotInfo(column="kurtosis", label="Kurtosis", colormap=COLORMAP),
    PlotInfo(column="max_absolute", label=REFLECTANCE_LABEL, colormap=COLORMAP),
]
OA_INFO = [
    PlotInfoOa(column="min_residual", colormap="rainbow_r"),
    PlotInfoOa(column="max_residual", colormap=COLORMAP),
    PlotInfoOa(column="percentile_90", colormap=COLORMAP),
    PlotInfoOa(column="percentile_99", colormap=COLORMAP),
    PlotInfoOa(column="percent_different", colormap=COLORMAP),
    PlotInfoOa(column="mean_residual", colormap="gist_rainbow"),
    PlotInfoOa(column="standard_deviation", colormap=COLORMAP),
    PlotInfoOa(column="skewness", colormap="gist_rainbow"),
    PlotInfoOa(column="kurtosis", colormap=COLORMAP),
    PlotInfoOa(column="max_absolute", colormap=COLORMAP),
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

    for plot_info in REFLECTANCE_INFO:

        prefix = Path(outdir, name.split("_")[0])
        if not prefix.exists():
            _LOG.info("creating output directory", outdir=str(prefix))
            prefix.mkdir(parents=True)

        out_fname = prefix.joinpath(f"{name}-{plot_info.column}.png")

        fig = plt.figure(figsize=(2.40, 2.40))
        axes = fig.add_subplot()

        # new rather than shared axes for colorbar
        divider = make_axes_locatable(axes)
        cax = divider.append_axes("right", size="5%", pad=0.1)

        norm = colors.Normalize(
            vmin=gdf_subset[plot_info.column].min(),
            vmax=gdf_subset[plot_info.column].max(),
        )
        colourbar = plt.cm.ScalarMappable(norm=norm, cmap=plot_info.colormap)

        ax_cbar = fig.colorbar(colourbar, cax=cax)

        # set sci formatting to 3 d.p. (aids in consistent plot sizes)
        ax_cbar.formatter.set_powerlimits((0, 3))
        ax_cbar.update_ticks()

        ax_cbar.set_label(plot_info.label, size=8)
        ax_cbar.ax.tick_params(labelsize=8)

        gdf_subset.plot(
            column=plot_info.column, cmap=plot_info.colormap, legend=False, ax=axes
        )

        tm_gdf.plot(linewidth=0.25, edgecolor="black", facecolor="none", ax=axes)

        axes.set_xlim(105, 160)
        axes.set_ylim(-45, -5)
        axes.set_xlabel("longitude")
        axes.set_ylabel("latitude")

        axes.xaxis.label.set_size(8)
        axes.yaxis.label.set_size(8)

        axes.tick_params(axis="x", labelsize=8)
        axes.tick_params(axis="y", labelsize=8)

        _LOG.info("saving figure as png", out_fname=str(out_fname))

        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
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
    specific_labels = {
        "kurtosis": "Kurtosis",
        "skewness": "Skewness",
        "percent_different": "% of Pixels where residiual != 0",
    }

    for plot_info in OA_INFO:
        prefix = Path(outdir, name.split("_")[0])
        if not prefix.exists():
            _LOG.info("creating output directory", outdir=str(prefix))
            prefix.mkdir(parents=True)

        label = labels.get(name, "Degrees")
        label = specific_labels.get(plot_info.column, label)

        out_fname = prefix.joinpath(f"{name}-{plot_info.column}.png")

        fig = plt.figure(figsize=(2.40, 2.40))
        axes = fig.add_subplot()

        # new rather than shared axes for colorbar
        divider = make_axes_locatable(axes)
        cax = divider.append_axes("right", size="5%", pad=0.1)

        norm = colors.Normalize(
            vmin=gdf_subset[plot_info.column].min(),
            vmax=gdf_subset[plot_info.column].max(),
        )
        colourbar = plt.cm.ScalarMappable(norm=norm, cmap=plot_info.colormap)

        ax_cbar = fig.colorbar(colourbar, cax=cax)

        # set sci formatting to 3 d.p. (aids in consistent plot sizes)
        ax_cbar.formatter.set_powerlimits((0, 3))
        ax_cbar.update_ticks()

        ax_cbar.set_label(label, size=8)
        ax_cbar.ax.tick_params(labelsize=8)

        gdf_subset.plot(
            column=plot_info.column, cmap=plot_info.colormap, legend=False, ax=axes
        )

        tm_gdf.plot(linewidth=0.25, edgecolor="black", facecolor="none", ax=axes)

        axes.set_xlim(105, 160)
        axes.set_ylim(-45, -5)
        axes.set_xlabel("longitude")
        axes.set_ylabel("latitude")

        axes.xaxis.label.set_size(8)
        axes.yaxis.label.set_size(8)

        axes.tick_params(axis="x", labelsize=8)
        axes.tick_params(axis="y", labelsize=8)

        _LOG.info("saving figure as png", out_fname=str(out_fname))

        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
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


def plot_proc_info_pngs(gdf: geopandas.GeoDataFrame, outdir: Path) -> None:
    """
    General plotting routine of the proc-info residuals analysis.
    """

    _LOG.info("reading the TM WORLD BORDERS dataset")

    with open(TM_WORLD_BORDERS_FNAME, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        tm_gdf = geopandas.read_file(dctx.stream_reader(src))

    if "aerosol" in gdf.columns:
        name = "ancillary"
        label = "{variable} difference"
    else:
        name = "gqa"
        label = "Pixels"

    skip = [
        "reference_pathname",
        "test_pathname",
        "region_code",
        "granule_id",
        "geometry",
    ]
    columns = [i for i in gdf.columns if i not in skip]

    for column in columns:
        prefix = Path(outdir, name)
        if not prefix.exists():
            _LOG.info("creating output directory", outdir=str(prefix))
            prefix.mkdir(parents=True)

        out_fname = prefix.joinpath(f"{name}-{column}.png")

        fig = plt.figure(figsize=(3, 3))
        axes = fig.add_subplot()

        norm = colors.Normalize(vmin=gdf[column].min(), vmax=gdf[column].max())
        colourbar = plt.cm.ScalarMappable(norm=norm, cmap="coolwarm")

        ax_cbar = fig.colorbar(colourbar, ax=axes)
        ax_cbar.set_label(label.format(variable=column))

        gdf.plot(column=column, cmap=COLORMAP, legend=False, ax=axes)

        tm_gdf.plot(linewidth=0.25, edgecolor="black", facecolor="none", ax=axes)

        axes.set_xlim(105, 160)
        axes.set_ylim(-45, -5)
        axes.set_xlabel("longitude")
        axes.set_ylabel("latitude")

        _LOG.info("saving figure as png", out_fname=str(out_fname))

        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        plt.savefig(out_fname, bbox_inches="tight")
        plt.close(fig)
