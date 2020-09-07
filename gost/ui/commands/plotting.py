"""
Command line interface for creating the PNG plots and the LaTeX documents.
"""
from pathlib import Path
from typing import Union
import click
import structlog  # type: ignore
import geopandas  # type: ignore

from gost.constants import (
    DirectoryNames,
    FileNames,
    LOG_PROCESSORS,
    LogNames,
)
from gost.plot_utils import plot_pngs
from gost.report_utils import latex_documents
from ._shared_commands import io_dir_options

_LOG = structlog.get_logger()


@click.command()
@io_dir_options
def plotting(
    outdir: Union[str, Path],
) -> None:
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
        reports_outdir = outdir.joinpath(DirectoryNames.REPORT.value)

        _LOG.info("producing PNG's")
        plot_pngs(gdf, plots_outdir)

        _LOG.info("producing LaTeX documents")
        latex_documents(gdf, reports_outdir)

        _LOG.info("finished producing plots and writing LaTeX documents")
