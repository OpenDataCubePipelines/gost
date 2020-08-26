from pathlib import Path
import click
import h5py
import structlog
from wagl.hdf5 import write_dataframe

from gost.constants import (
    DatasetNames,
    DirectoryNames,
    FileNames,
    LOG_PROCESSORS,
    LogNames,
)
from gost.query import query_products, query_via_filepath
from ._shared_commands import io_dir_options, db_query_options


structlog.configure(processors=LOG_PROCESSORS)
_LOG = structlog.get_logger()


@click.command(
    name="query",
    help="Query the test and reference products to be used in the intercomparison",
)
@io_dir_options
@db_query_options
def query(
    outdir,
    product_name_test,
    product_name_reference,
    db_env_test,
    db_env_reference,
    time,
    lon,
    lat,
    additional_filters,
):
    """
    Database querying of test and reference products.
    """

    outdir = Path(outdir)
    log_fname = outdir.joinpath(DirectoryNames.LOGS.value, LogNames.QUERY.value)

    if not log_fname.parent.exists():
        log_fname.parent.mkdir()

    with open(log_fname, "w") as fobj:
        structlog.configure(logger_factory=structlog.PrintLoggerFactory(fobj))

        results = query_products(
            product_name_test,
            product_name_reference,
            db_env_test,
            db_env_reference,
            time,
            lon,
            lat,
            additional_filters,
        )

        results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.RESULTS.value
        )
        dataset_name = DatasetNames.QUERY.value

        _LOG.info(
            "saving results of query",
            out_fname=str(results_fname),
            dataset_name=dataset_name,
        )

        with h5py.File(str(results_fname), "w") as fid:
            write_dataframe(results, dataset_name, fid)


@click.command(
    name="query-filesystem",
    help="Query the test and reference products to be used in the intercomparison",
)
@io_dir_options
@click.option(
    "--product-pathname-test",
    type=click.STRING,
    required=True,
    help="Pathname to the test product, eg '/g/data/xu18/ga/ga_ls8c_ard_3' ",
)
@click.option(
    "--product-pathname-reference",
    type=click.STRING,
    required=True,
    help="Pathname to the reference product, eg '/g/data/u46/ga/ga_ls8c_ard_3' ",
)
@click.option(
    "--glob-pattern-test",
    type=click.STRING,
    required=True,
    help="Pattern to glob for the test product, eg '*/*/2019/05/*/*.odc-metadata.yaml' ",
)
@click.option(
    "--glob-pattern-reference",
    type=click.STRING,
    required=True,
    help="Pattern to glob for the reference product, eg '*/*/2019/05/*/*.odc-metadata.yaml' ",
)
def query_filesystem(
    outdir,
    product_pathname_test,
    product_pathname_reference,
    glob_pattern_test,
    glob_pattern_reference,
):
    """
    Filesystem querying of test and reference products.
    """

    outdir = Path(outdir)
    log_fname = outdir.joinpath(DirectoryNames.LOGS.value, LogNames.QUERY.value)

    if not log_fname.parent.exists():
        log_fname.parent.mkdir()

    with open(log_fname, "w") as fobj:
        structlog.configure(logger_factory=structlog.PrintLoggerFactory(fobj))

        results = query_via_filepath(
            product_pathname_test,
            product_pathname_reference,
            glob_pattern_test,
            glob_pattern_reference,
        )

        results_fname = outdir.joinpath(
            DirectoryNames.RESULTS.value, FileNames.RESULTS.value
        )
        dataset_name = DatasetNames.QUERY.value

        _LOG.info(
            "saving results of query",
            out_fname=str(results_fname),
            dataset_name=dataset_name,
        )

        with h5py.File(str(results_fname), "w") as fid:
            write_dataframe(results, dataset_name, fid)
