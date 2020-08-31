from pathlib import Path
import click
import structlog
import geopandas

from gost.constants import (
    DirectoryNames,
    FileNames,
    LOG_PROCESSORS,
    LogNames,
)
from gost.plot_utils import plot_png
from ._shared_commands import io_dir_options, db_query_options

_LOG = structlog.get_logger()


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

        plot_png(gdf, outdir)
