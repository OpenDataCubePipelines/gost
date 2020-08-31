from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import geopandas
import structlog
import zstandard

from gost.constants import TM_WORLD_BORDERS_FNAME

COLUMNS = [
    "min_residual",
    "max_residual",
    "percentile_90",
    "percentile_99",
    "percent_different",
]
_LOG = structlog.get_logger()


def plot_png(gdf, outdir):
    """
    General plotting routine of the residuals analysis.
    Currently only interested in the surface reflectance measurements,
    but can easily be expanded to to incorporate other measurements.
    """
    # read the TM_WORLD_BORDERS dataset
    with open(TM_WORLD_BORDERS_FNAME, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        tm_gdf = geopandas.read_file(dctx.stream_reader(src))

    for name, grp in gdf.groupby("measurement"):

        if "nbar" not in name:
            # only deal with reflectance measurements for now
            _LOG.info("skipping measurement", measurement_name=name)
            continue

        for column in COLUMNS:
            if "percent_different" in column:
                label = "% of Pixels where residiual != 0"
            else:
                label = "% Reflectance"

            if "min_residual" in column:
                # reverse so red indicates greater change
                colourmap = "rainbow_r"
            else:
                colourmap = "rainbow"

            prefix = Path(outdir, name.split("_")[0])
            if not prefix.exists():
                _LOG.info("creating output directory", outdir=str(prefix))
                prefix.mkdir(parents=True)

            out_fname = prefix.joinpath("{}-{}.png".format(name, column))

            fig = plt.figure(figsize=(3, 3))
            axes = fig.add_subplot()

            gdf.plot(column=column, cmap=colourmap, legend=False, ax=axes)

            norm = colors.Normalize(vmin=gdf[column].min(), vmax=gdf[column].max())
            colourbar = plt.cm.ScalarMappable(norm=norm, cmap=colourmap)

            ax_cbar = fig.colorbar(colourbar, ax=axes)
            ax_cbar.set_label(label)

            grp.plot(column=column, cmap="rainbow", legend=False, ax=axes)

            tm_gdf.plot(linewidth=0.25, edgecolor="black", facecolor="none", ax=axes)

            axes.set_xlim(105, 160)
            axes.set_ylim(-45, -5)
            axes.set_xlabel("longitude")
            axes.set_ylabel("latitude")

            _LOG.info("saving figure as png", out_fname=str(out_fname))

            plt.savefig(out_fname, bbox_inches="tight")
            plt.close(fig)
