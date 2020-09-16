from pathlib import Path
import click
import h5py
import structlog

from wagl.hdf5 import read_h5_table, write_dataframe
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

        with h5py.File(str(comparison_results_fname), "a") as fid:
            for dataset_name in DatasetNames:
                if dataset_name == DatasetNames.QUERY:
                    continue

                _LOG.info("reading dataset", dataset_name=dataset_name.value)
                dataframe = read_h5_table(fid, dataset_name.value)

                dataset = fid[dataset_name.value]
                framing = dataset.attrs["framing"]
                thematic = dataset.attrs["thematic"]
                proc_info = dataset.attrs["proc-info"]

                _LOG.info(
                    "merging results with framing",
                    framing=framing,
                    dataset_name=dataset_name.value,
                )

                geo_dataframe = merge_framing(dataframe, framing)

                out_fname = outdir.joinpath(
                    DirectoryNames.RESULTS.value,
                    FileNames[MergeLookup[dataset_name.name].value].value,
                )

                _LOG.info("saving as GeoJSON", out_fname=str(out_fname))
                geo_dataframe.to_file(str(out_fname), driver="GeoJSONSeq")

                _LOG.info("summarising")

                summary_dataframe = summarise(geo_dataframe, thematic, proc_info)

                out_dname = DatasetNames[SummaryLookup[dataset_name.name].value].value

                _LOG.info("saving summary table", out_dataset_name=out_dname)
                write_dataframe(summary_dataframe, out_dname, fid)

                if not thematic and not proc_info:
                    _LOG.info("undertaking reflectance evaluation")
                    cols = [
                        i
                        for i in summary_dataframe.index.get_level_values(0)
                        if "nbar" in i
                    ]
                    result = summary_dataframe.loc[
                        (cols, ["max_residual", "min_residual"]), :
                    ]

                    out_dname = DatasetNames[
                        SummaryLookup[dataset_name.name].value
                    ].value

                    _LOG.info("saving summary table", out_dataset_name=out_dname)
                    write_dataframe(result, out_dname, fid)

                    minv = result.min(axis=0)["amin"]
                    maxv = result.max(axis=0)["amax"]

                    test_passed = max(abs(minv), abs(maxv)) <= 1

                    _LOG.info(
                        "final reflectance evaluation",
                        test_passed=test_passed,
                        min_residual=minv,
                        max_residual=maxv,
                    )
