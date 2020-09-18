"""
Command line interface for creating the LaTeX documents.
"""
from pathlib import Path, PurePosixPath as PPath
from typing import Union
import click
import h5py  # type: ignore
import structlog  # type: ignore
import geopandas  # type: ignore

from wagl.hdf5 import read_h5_table  # type: ignore
from gost.constants import (
    DatasetGroups,
    DatasetNames,
    DirectoryNames,
    FileNames,
    LOG_PROCESSORS,
    LogNames,
)
from gost.collate import create_general_csvs, create_csv
from gost.report_utils import latex_documents
from ._shared_commands import io_dir_options

_LOG = structlog.get_logger()


@click.command()
@io_dir_options
def reporting(
    outdir: Union[str, Path],
) -> None:
    """
    Produce the LaTeX reports, and final pass/fail summary.
    """

    outdir = Path(outdir)
    log_fname = outdir.joinpath(DirectoryNames.LOGS.value, LogNames.REPORTING.value)

    if not log_fname.parent.exists():
        log_fname.parent.mkdir(parents=True)

    with open(log_fname, "w") as fobj:
        structlog.configure(
            logger_factory=structlog.PrintLoggerFactory(fobj), processors=LOG_PROCESSORS
        )

        comparison_results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.RESULTS.value
        )

        _LOG.info(
            "opening intercomparison results file", fname=str(comparison_results_fname)
        )

        with h5py.File(str(comparison_results_fname), "r") as fid:
            # read intercomparison general measurements summary
            dataset_name = PPath(
                DatasetGroups.SUMMARY.value, DatasetNames.GENERAL_SUMMARISED.value
            )
            _LOG.info("reading dataset", dataset_name=str(dataset_name))
            dataframe = read_h5_table(fid, str(dataset_name))

            # read intercomparison ancillary summary
            dataset_name = PPath(
                DatasetGroups.SUMMARY.value, DatasetNames.ANCILLARY_SUMMARISED.value
            )
            _LOG.info("reading dataset", dataset_name=str(dataset_name))
            ancillary_df = read_h5_table(fid, str(dataset_name))

            # read intercomparison gqa summary
            dataset_name = PPath(
                DatasetGroups.SUMMARY.value, DatasetNames.GQA_SUMMARISED.value
            )
            _LOG.info("reading dataset", dataset_name=str(dataset_name))
            gqa_df = read_h5_table(fid, str(dataset_name))

            dataset_name = PPath(DatasetNames.SOFTWARE_VERSIONS.value)
            _LOG.info("reading dataset", dataset_name=str(dataset_name))
            software_df = read_h5_table(fid, dataset_name)


        _LOG.info("creating CSV's of the general measurements intercomparison summary")
        create_general_csvs(dataframe, outdir.joinpath(DirectoryNames.RESULTS.value))

        _LOG.info("creating CSV of the ancillary intercomparison summary")
        out_fname = outdir.joinpath(DirectoryNames.RESULTS.value, "ancillary_min_max.csv")
        create_csv(ancillary_df, out_fname)

        _LOG.info("creating CSV of the gqa intercomparison summary")
        out_fname = outdir.joinpath(DirectoryNames.RESULTS.value, "gqa_min_max.csv")
        create_csv(gqa_df, out_fname)

        _LOG.info("creating CSV of the software versions")
        out_fname = outdir.joinpath(DirectoryNames.RESULTS.value, "software-versions.csv")
        software_df.to_csv(out_fname, index=False)

        results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.GENERAL_FRAMING.value
        )

        _LOG.info(
            "opening geometry framing general results file", fname=str(results_fname)
        )
        gdf = geopandas.read_file(results_fname)

        reports_outdir = outdir.joinpath(DirectoryNames.REPORT.value)

        _LOG.info("producing LaTeX documents of general results")
        latex_documents(gdf, dataframe, reports_outdir)

        # TODO GQA and ancillary

        _LOG.info("finished writing the LaTeX documents")
