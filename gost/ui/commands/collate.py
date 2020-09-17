"""
Command line interface for collating the results of the intercomparison
analysis.
"""
from pathlib import Path, PurePosixPath as PPath
from typing import Union
import click
import h5py  # type: ignore
import structlog  # type: ignore

from wagl.hdf5 import read_h5_table, write_dataframe  # type: ignore
from gost.constants import (
    DatasetGroups,
    DatasetNames,
    DirectoryNames,
    FileNames,
    LOG_PROCESSORS,
    LogNames,
    MergeLookup,
    SummaryLookup,
)
from gost.collate import merge_framing, summarise
from ._shared_commands import io_dir_options


_LOG = structlog.get_logger()


@click.command()
@io_dir_options
def collate(outdir: Union[str, Path]) -> None:
    """
    Collate the results of the product comparison.
    Firstly the results are merged with the framing geometry, and second
    they're summarised.
    """

    outdir = Path(outdir)
    log_fname = outdir.joinpath(DirectoryNames.LOGS.value, LogNames.COLLATE.value)

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

        with h5py.File(str(comparison_results_fname), "a") as fid:
            grp = fid[DatasetGroups.INTERCOMPARISON.value]

            for dataset_name in grp:
                _LOG.info("reading dataset", dataset_name=dataset_name)
                dataframe = read_h5_table(grp, dataset_name)

                # some important attributes
                framing = grp[dataset_name].attrs["framing"]
                thematic = grp[dataset_name].attrs["thematic"]
                proc_info = grp[dataset_name].attrs["proc-info"]

                _LOG.info(
                    "merging results with framing",
                    framing=framing,
                    dataset_name=dataset_name,
                )

                geo_dataframe = merge_framing(dataframe, framing)

                out_fname = outdir.joinpath(
                    DirectoryNames.RESULTS.value,
                    FileNames[MergeLookup[DatasetNames(dataset_name).name].value].value,
                )

                _LOG.info("saving as GeoJSON", out_fname=str(out_fname))
                geo_dataframe.to_file(str(out_fname), driver="GeoJSONSeq")

                _LOG.info("summarising")

                summary_dataframe = summarise(geo_dataframe, thematic, proc_info)

                out_dname = PPath(
                    DatasetGroups.SUMMARY.value,
                    DatasetNames[
                        SummaryLookup[DatasetNames(dataset_name).name].value
                    ].value,
                )

                _LOG.info("saving summary table", out_dataset_name=str(out_dname))
                write_dataframe(summary_dataframe, str(out_dname), fid)
