from pathlib import Path
import click
import h5py
import structlog

from wagl.hdf5 import read_h5_table
from gost.constants import (
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
def collate(outdir: str) -> None:
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

        with h5py.File(str(comparison_results_fname), "r") as fid:
            for dataset_name in DatasetNames:
                if dataset_name == DatasetNames.QUERY:
                    continue

                _LOG.info("reading dataset", dataset_name=dataset_name.value)
                dataframe = read_h5_table(fid, dataset_name.value)

                dataset = fid[dataset_name.value]
                framing = dataset.attrs["framing"]
                thematic = dataset.attrs["thematic"]

                _LOG.info(
                    "merging results with framing",
                    framing=framing,
                    dataset_name=dataset_name.value,
                )

                # TODO; add the framing name as an attr to the dataset or similar
                geo_dataframe = merge_framing(dataframe, framing)

                out_fname = outdir.joinpath(
                    DirectoryNames.RESULTS.value,
                    FileNames[MergeLookup[dataset_name.name].value].value,
                )

                _LOG.info("saving as GeoJSON", out_fname=str(out_fname))
                geo_dataframe.to_file(str(out_fname), driver="GeoJSONSeq")

                # if dataset_name == DatasetNames.GQA_RESULTS:
                #     _LOG.info("skipping summarising task for GQA results")
                #     continue

                _LOG.info("summarising")

                summary_dataframe = summarise(geo_dataframe, thematic)

                out_fname = outdir.joinpath(
                    DirectoryNames.RESULTS.value,
                    FileNames[SummaryLookup[dataset_name.name].value].value,
                )

                _LOG.info("saving summary as CSV", out_fname=str(out_fname))
                summary_dataframe.to_csv(str(out_fname))
