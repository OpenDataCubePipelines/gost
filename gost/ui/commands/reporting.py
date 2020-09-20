"""
Command line interface for creating the LaTeX documents.
"""
from pathlib import Path, PurePosixPath as PPath
from typing import Union
import click
import h5py  # type: ignore
import pandas
import structlog  # type: ignore
import geopandas  # type: ignore

from wagl.hdf5 import read_h5_table  # type: ignore
from gost.constants import (
    CsvFileNames,
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


def _extract_proc_info_results(fid: h5py.File, outdir: Path) -> None:
    """
    Extracts the ancillary, gqa, software versions results tables
    and converts to CSV for the LaTeX document.
    """

    def _read_table(fid: h5py.File, dataset_name: PPath) -> pandas.DataFrame:
        """Small proxy to read the H5 table dataset."""

        _LOG.info("reading dataset", dataset_name=str(dataset_name))
        dataframe = read_h5_table(fid, str(dataset_name))

        return dataframe

    dataset_name = PPath(
        DatasetGroups.SUMMARY.value, DatasetNames.ANCILLARY_SUMMARISED.value
    )
    ancillary_df = _read_table(fid, dataset_name)

    dataset_name = PPath(DatasetGroups.SUMMARY.value, DatasetNames.GQA_SUMMARISED.value)
    gqa_df = _read_table(fid, dataset_name)

    dataset_name = PPath(DatasetNames.SOFTWARE_VERSIONS.value)
    software_df = _read_table(fid, dataset_name)

    out_fname = outdir.joinpath(
        DirectoryNames.RESULTS.value, CsvFileNames.ANCILLARY.value
    )
    create_csv(ancillary_df, out_fname)

    out_fname = outdir.joinpath(DirectoryNames.RESULTS.value, CsvFileNames.GQA.value)
    create_csv(gqa_df, out_fname)

    out_fname = outdir.joinpath(
        DirectoryNames.RESULTS.value, CsvFileNames.SOFTWARE.value
    )
    _LOG.info("writing CSV", out_fname=str(out_fname))
    software_df.to_csv(out_fname, index=False)


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

            # read and convert metadata tables
            _extract_proc_info_results(fid, outdir)

        _LOG.info("creating CSV's of the general measurements intercomparison summary")
        create_general_csvs(dataframe, outdir.joinpath(DirectoryNames.RESULTS.value))

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
