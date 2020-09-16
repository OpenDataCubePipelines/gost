from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import click
import h5py  # type: ignore
from mpi4py import MPI  # type: ignore
import pandas  # type: ignore
import structlog  # type: ignore

from mpi_structlog.mpi_logger import DEFAULT_PROCESSORS, MPIStreamIO, MPILoggerFactory  # type: ignore
from wagl.tiling import scatter  # type: ignore
from wagl.hdf5 import read_h5_table, write_dataframe  # type: ignore

from gost.constants import (
    DatasetNames,
    DirectoryNames,
    FileNames,
    LogNames,
)
from gost import compare_measurements, compare_proc_info
from gost.odc_documents import load_odc_metadata, Granule
from ._shared_commands import io_dir_options

# comm info
COMM = MPI.COMM_WORLD

_LOG = structlog.get_logger()


def _concatenate_records(records: Union[List[Any], None]) -> pandas.DataFrame:
    """Concatenates a list of dicts into a pandas.DataFrame."""

    if records:
        dataframe = pandas.DataFrame(records[0])
        for record in records[1:]:
            dataframe = dataframe.append(pandas.DataFrame(record))

        _LOG.info("reset dataframe index")

        dataframe.reset_index(drop=True, inplace=True)

    else:
        dataframe = pandas.DataFrame()

    return dataframe


def _process_proc_info(
    dataframe: pandas.DataFrame, rank: int
) -> Tuple[Optional[pandas.DataFrame], Optional[pandas.DataFrame]]:
    gqa_results, ancillary_results = compare_proc_info.process_yamls(dataframe)

    # gather proc info results from each worker
    if rank == 0:
        _LOG.info("gathering gqa field records from all workers")

    gqa_records = COMM.gather(gqa_results, root=0)

    if rank == 0:
        _LOG.info("gathering gqa field records from all workers")

    ancillary_records = COMM.gather(ancillary_results, root=0)

    if rank == 0:
        _LOG.info("appending proc-info dataframes")

        gqa_df = _concatenate_records(gqa_records)
        ancillary_df = _concatenate_records(ancillary_records)

    else:
        gqa_df = pandas.DataFrame()
        ancillary_df = pandas.DataFrame()

    return gqa_df, ancillary_df


def _process_odc_doc(dataframe: pandas.DataFrame, rank: int) -> Tuple[Any, ...]:
    results = compare_measurements.process_yamls(dataframe)

    # gather records from all workers
    if rank == 0:
        _LOG.info("gathering measurement records from all workers")

    general_records = COMM.gather(results[0], root=0)
    fmask_records = COMM.gather(results[1], root=0)
    contiguity_records = COMM.gather(results[2], root=0)
    shadow_records = COMM.gather(results[3], root=0)

    # create dataframes for each set of results
    if rank == 0:
        _LOG.info("appending dataframes")

        general_df = _concatenate_records(general_records)
        fmask_df = _concatenate_records(fmask_records)
        contiguity_df = _concatenate_records(contiguity_records)
        shadow_df = _concatenate_records(shadow_records)

    else:
        general_df = pandas.DataFrame()
        fmask_df = pandas.DataFrame()
        contiguity_df = pandas.DataFrame()
        shadow_df = pandas.DataFrame()

    return general_df, fmask_df, contiguity_df, shadow_df


@click.command()
@io_dir_options
@click.option(
    "--proc-info",
    default=False,
    is_flag=True,
    help="If set, then comapre the GQA fields and not the product measurements",
)
def comparison(outdir: Union[str, Path], proc_info: bool) -> None:
    """
    Test and Reference product intercomparison evaluation.
    """

    outdir = Path(outdir)
    if proc_info:
        log_fname = outdir.joinpath(
            DirectoryNames.LOGS.value, LogNames.PROC_INFO_INTERCOMPARISON.value
        )
    else:
        log_fname = outdir.joinpath(
            DirectoryNames.LOGS.value, LogNames.MEASUREMENT_INTERCOMPARISON.value
        )

    out_stream = MPIStreamIO(str(log_fname))
    structlog.configure(
        processors=DEFAULT_PROCESSORS, logger_factory=MPILoggerFactory(out_stream)
    )

    # processor info
    rank = COMM.Get_rank()
    n_processors = COMM.Get_size()

    results_fname = outdir.joinpath(
        DirectoryNames.RESULTS.value, FileNames.RESULTS.value
    )

    with h5py.File(str(results_fname), "r") as fid:
        dataframe = read_h5_table(fid, DatasetNames.QUERY.value)

    if rank == 0:
        index = dataframe.index.values.tolist()
        blocks = scatter(index, n_processors)

        # some basic attribute information
        doc: Union[Granule, None] = load_odc_metadata(
            Path(dataframe.iloc[0].yaml_pathname_reference)
        )
        attrs: Dict[str, Any] = {
            "framing": doc.framing,
            "thematic": False,
            "proc-info": False,
        }
    else:
        blocks = None
        doc = None
        attrs = dict()

    COMM.Barrier()

    # equally partition the work across all procesors
    indices = COMM.scatter(blocks, root=0)

    if proc_info:
        attrs["proc-info"] = True
        if rank == 0:
            _LOG.info("procssing proc-info documents")

        gqa_dataframe, ancillary_dataframe = _process_proc_info(
            dataframe.iloc[indices], rank
        )

        if rank == 0:
            _LOG.info("saving gqa dataframe results to tables")

            if not results_fname.parent.exists():
                results_fname.parent.mkdir(parents=True)

            with h5py.File(str(results_fname), "a") as fid:
                write_dataframe(
                    gqa_dataframe, DatasetNames.GQA_RESULTS.value, fid, attrs=attrs
                )

            _LOG.info("saving ancillary dataframe results to tables")

            if not results_fname.parent.exists():
                results_fname.parent.mkdir(parents=True)

            with h5py.File(str(results_fname), "a") as fid:
                write_dataframe(
                    ancillary_dataframe,
                    DatasetNames.ANCILLARY_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

    else:
        if rank == 0:
            _LOG.info("processing odc-metadata documents")
        results = _process_odc_doc(dataframe.iloc[indices], rank)

        if rank == 0:
            # save each table
            _LOG.info("saving dataframes to tables")
            with h5py.File(str(results_fname), "a") as fid:
                attrs["thematic"] = False
                write_dataframe(
                    results[0],
                    DatasetNames.GENERAL_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

                attrs["thematic"] = True
                write_dataframe(
                    results[1],
                    DatasetNames.FMASK_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

                write_dataframe(
                    results[2],
                    DatasetNames.CONTIGUITY_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

                write_dataframe(
                    results[3],
                    DatasetNames.SHADOW_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

    if rank == 0:
        workflow = "proc-info field" if proc_info else "product measurement"
        msg = f"{workflow} comparison processing finished"
        _LOG.info(msg)
