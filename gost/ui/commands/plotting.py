import io
from pathlib import Path
import click
import structlog
import geopandas
import zstandard

from gost.constants import (
    DirectoryNames,
    FileNames,
    LOG_PROCESSORS,
    LogNames,
    LANDSAT_LATEX_TEMPLATE_FNAME,
    LANDSAT_CA_LATEX_TEMPLATE_FNAME,
)
from gost.plot_utils import plot_png
from ._shared_commands import io_dir_options

_LOG = structlog.get_logger()


def _latex_documents(coastal=False):
    """Utility to create the latex document strings."""

    _LOG.info("reading Landsat LaTeX template")

    with open(LANDSAT_LATEX_TEMPLATE_FNAME, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        landsat_template = io.TextIOWrapper(
            dctx.stream_reader(src), encoding="utf-8"
        ).read()

    if coastal:
        _LOG.info("reading Landsat coastal aerosol LaTeX template")
        with open(LANDSAT_CA_LATEX_TEMPLATE_FNAME, "rb") as src:
            dctx = zstandard.ZstdDecompressor()
            coastal_template = io.TextIOWrapper(
                dctx.stream_reader(src), encoding="utf-8"
            ).read()

        nbar_document = landsat_template.format(
            sr_type="nbar",
            SR_TYPE="NBAR",
            coastal_aerosol=coastal_template.format(sr_type="nbar", SR_TYPE="NBAR"),
        )
        nbart_document = landsat_template.format(
            sr_type="nbart",
            SR_TYPE="NBART",
            coastal_aerosol=coastal_template.format(sr_type="nbart", SR_TYPE="NBART"),
        )
    else:
        nbar_document = landsat_template.format(
            sr_type="nbar",
            SR_TYPE="NBAR",
        )
        nbart_document = landsat_template.format(
            sr_type="nbart",
            SR_TYPE="NBART",
        )

    return nbar_document, nbart_document


@click.command()
@io_dir_options
def plotting(
    outdir,
):
    """
    Using the framing geometry, plot the results of the intercomparison evaluation.
    """

    outdir = Path(outdir)
    log_fname = outdir.joinpath(DirectoryNames.LOGS.value, LogNames.PLOTTING.value)

    if not log_fname.parent.exists():
        log_fname.parent.mkdir(parents=True)

    with open(log_fname, "w") as fobj:
        structlog.configure(
            logger_factory=structlog.PrintLoggerFactory(fobj), processors=LOG_PROCESSORS
        )

        results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.GENERAL_FRAMING.value
        )

        _LOG.info("opening geometry framing results file", fname=str(results_fname))
        gdf = geopandas.read_file(results_fname)

        plots_outdir = outdir.joinpath(DirectoryNames.PLOTS.value)
        plot_png(gdf, plots_outdir)

        # this needs reworking so we can cater for sentinel-2
        granule = gdf.iloc[0].granule

        if "LC8" in granule:
            coastal = True

        nbar_document, nbart_document = _latex_documents(coastal)

        # output filenames
        nbar_out_fname = outdir.joinpath(
            DirectoryNames.REPORT.value, FileNames.NBAR_REPORT.value
        )
        nbart_out_fname = outdir.joinpath(
            DirectoryNames.REPORT.value, FileNames.NBART_REPORT.value
        )

        if not nbar_out_fname.parent.exists():
            _LOG.info(
                "creating report output directory", outdir=str(nbar_out_fname.parent)
            )
            nbar_out_fname.parent.mkdir(parents=True)

        _LOG.info("writing NBAR LaTeX document", out_fname=str(nbar_out_fname))

        with open(nbar_out_fname, "w") as src:
            src.write(nbar_document)

        _LOG.info("writing NBART LaTeX document", out_fname=str(nbart_out_fname))

        with open(nbart_out_fname, "w") as src:
            src.write(nbart_document)
