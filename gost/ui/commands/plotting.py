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
from gost.plot_utils import plot_pngs, plot_proc_info_pngs
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

        _LOG.info(
            "opening geometry framing general results file", fname=str(results_fname)
        )
        gdf = geopandas.read_file(results_fname)

        plots_outdir = outdir.joinpath(DirectoryNames.PLOTS.value)

        _LOG.info("producing general results PNG's")
        plot_pngs(gdf, plots_outdir)

        # GQA and ancillary pngs

        results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.GQA_FRAMING.value
        )

        _LOG.info("opening geometry framing gqa results file", fname=str(results_fname))
        gdf = geopandas.read_file(results_fname)

        _LOG.info("producing gqa PNG's")
        plot_proc_info_pngs(gdf, plots_outdir)

        results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.ANCILLARY_FRAMING.value
        )

        _LOG.info(
            "opening geometry framing ancillary results file", fname=str(results_fname)
        )
        gdf = geopandas.read_file(results_fname)

        _LOG.info("producing ancillary PNG's")
        plot_proc_info_pngs(gdf, plots_outdir)

        _LOG.info("finished producing plots")
