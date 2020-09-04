from pathlib import Path
import click
import h5py
from mpi4py import MPI
import pandas
import structlog
from typing import Any, Optional, Tuple

from mpi_structlog.mpi_logger import DEFAULT_PROCESSORS, MPIStreamIO, MPILoggerFactory
from wagl.tiling import scatter
from wagl.hdf5 import read_h5_table, write_dataframe

from gost.constants import (
    DatasetNames,
    DirectoryNames,
    FileNames,
    LogNames,
    MergeLookup,
    SummaryLookup,
)
from gost import compare_measurements, compare_gqa
from gost.odc_documents import Digestyaml
from ._shared_commands import io_dir_options, db_query_options

# comm info
COMM = MPI.COMM_WORLD

_LOG = structlog.get_logger()


def _process_proc_info(dataframe: pandas.DataFrame, rank: int) -> Optional[pandas.DataFrame]:
    gqa_results = compare_gqa.process_yamls(dataframe)

    # gather proc info results from each worker
    if rank == 0:
        _LOG.info("gathering gqa field records from all workers")

    gqa_records = COMM.gather(gqa_results, root=0)

    if rank == 0:
        _LOG.info("appending proc-info dataframes")

        if gqa_records:
            gqa_df = pandas.DataFrame(gqa_records[0])
            for record in gqa_records[1:]:
                gqa_df = gqa_df.append(pandas.DataFrame(record))

            # reset to a unique index
            _LOG.info("reset gqa results dataframe index")
            gqa_df.reset_index(drop=True, inplace=True)

        else:
            gqa_df = pandas.DataFrame()

    else:
        gqa_df = None

    return gqa_df


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
        if general_records:
            general_df = pandas.DataFrame(general_records[0])
            for record in general_records[1:]:
                general_df = general_df.append(pandas.DataFrame(record))

            _LOG.info("reset general dataframe index")
            general_df.reset_index(drop=True, inplace=True)

        else:
            general_df = pandas.DataFrame()

        if fmask_records:
            fmask_df = pandas.DataFrame(fmask_records[0])
            for record in fmask_records[1:]:
                fmask_df = fmask_df.append(pandas.DataFrame(record))

            _LOG.info("reset fmask dataframe index")
            fmask_df.reset_index(drop=True, inplace=True)

        else:
            fmask_df = pandas.DataFrame()

        if contiguity_records:
            contiguity_df = pandas.DataFrame(contiguity_records[0])
            for record in contiguity_records[1:]:
                contiguity_df = contiguity_df.append(pandas.DataFrame(record))

            _LOG.info("reset contiguity dataframe index")
            contiguity_df.reset_index(drop=True, inplace=True)

        else:
            contiguity_df = pandas.DataFrame()

        if shadow_records:
            shadow_df = pandas.DataFrame(shadow_records[0])
            for record in shadow_records[1:]:
                shadow_df = shadow_df.append(pandas.DataFrame(record))

            _LOG.info("reset shadow dataframe index")
            shadow_df.reset_index(drop=True, inplace=True)

        else:
            shadow_df = pandas.DataFrame()

    else:
        general_df = None
        fmask_df = None
        contiguity_df = None
        shadow_df = None

    return general_df, fmask_df, contiguity_df, shadow_df


@click.command()
@io_dir_options
@click.option(
    "--compare-gqa",
    default=False,
    is_flag=True,
    help="If set, then comapre the GQA fields and not the product measurements",
)
def comparison(outdir: str, compare_gqa: bool) -> None:
    """
    Test and Reference product intercomparison evaluation.
    """

    outdir = Path(outdir)
    if compare_gqa:
        log_fname = outdir.joinpath(
            DirectoryNames.LOGS.value, LogNames.GQA_INTERCOMPARISON.value
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
        doc = Digestyaml(dataframe.iloc[0].yaml_pathname_reference)
        attrs = {"framing": doc.framing, "thematic": False}
    else:
        blocks = None
        doc = None
        attrs = None

    COMM.Barrier()

    # equally partition the work across all procesors
    indices = COMM.scatter(blocks, root=0)

    if compare_gqa:
        if rank == 0:
            _LOG.info("procssing proc-info documents")

        gqa_dataframe = _process_proc_info(dataframe.iloc[indices], rank)

        if rank == 0:
            _LOG.info("saving gqa dataframe results to tables")

            if not results_fname.parent.exists():
                results_fname.parent.mkdir(parents=True)

            with h5py.File(str(results_fname), "a") as fid:
                write_dataframe(
                    gqa_dataframe, DatasetNames.GQA_RESULTS.value, fid, attrs=attrs
                )

    else:
        if rank == 0:
            _LOG.info("processing odc-metadata documents")
        results = _process_odc_doc(dataframe.iloc[indices], rank)

        general_dataframe = results[0]
        fmask_dataframe = results[1]
        contiguity_dataframe = results[2]
        shadow_dataframe = results[3]

        if rank == 0:
            # save each table
            _LOG.info("saving dataframes to tables")
            with h5py.File(str(results_fname), "a") as fid:
                attrs["thematic"] = False
                write_dataframe(
                    general_dataframe,
                    DatasetNames.GENERAL_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

                attrs["thematic"] = True
                write_dataframe(
                    fmask_dataframe, DatasetNames.FMASK_RESULTS.value, fid, attrs=attrs,
                )

                attrs["thematic"] = True
                write_dataframe(
                    contiguity_dataframe,
                    DatasetNames.CONTIGUITY_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

                attrs["thematic"] = True
                write_dataframe(
                    shadow_dataframe,
                    DatasetNames.SHADOW_RESULTS.value,
                    fid,
                    attrs=attrs,
                )

    if rank == 0:
        workflow = "gqa field" if compare_gqa else "product measurement"
        msg = "{} comparison processing finished".format(workflow)
        _LOG.info(msg)
