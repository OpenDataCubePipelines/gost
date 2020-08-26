"""
Module for querying the reference and test products that will be used
in the intercomparison evaluation.
As the test or reference datasets might be missing some records, we
need to perform an inner join such that there is a 1-1 relationship.
Product names can be different, database environments can be different;
However, both must have their level-1 ancestor uuid available in the
yaml document for a given dataset. If not, that dataset record will be
removed from the resulting query.
"""

from pathlib import Path
import datacube
import pandas
import structlog

from gost.digest_yaml import Digestyaml

_LOG = structlog.get_logger()


def query_db(env, product_name, time, lon, lat, additional_filters):
    """
    Generic datacube query wrapper.

    :param env:
        Name of the database environment to query.

    :param product_name:
        Name of the product to query.

    :param time:
        The time (earliest, latest) extents (optional).

    :param lon:
        The longitude (left, right) extents (optional).

    :param lat:
        The latitude (top, bottom) extents (optional).

    :param additional_filters:
        A dictionary containing {field: value} pairs that datacube can
        use to further filter datasets (optional).
        e.g. {"region_code": "092084"}
    """

    dc = datacube.Datacube(env=env)

    _LOG.info(
        "finding datasets",
        env=env,
        product_name=product_name,
        time=time,
        lon=lon,
        lat=lat,
    )
    datasets = dc.find_datasets(
        product_name, time=time, lon=lon, lat=lat, **additional_filters
    )

    uuid = []
    yaml_pathname = []
    proc_info_pathname = []

    for dataset in datasets:
        _LOG.info("processing dataset", dataset=str(dataset.local_path))
        doc = Digestyaml(dataset.local_path)

        uuid.append(doc.parent_uuid)
        yaml_pathname.append(str(dataset.local_path))

        # procssing info document
        proc_info_pathname = dataset.local_path.parent.joinpath(
            dataset.metadata_doc["accessories"]["metadata:processor"]["path"]
        )
        proc_info_pathname.append(str(proc_info_pathname))

    dataframe = pandas.DataFrame(
        {
            "level1_uuid": uuid,
            "yaml_pathname": yaml_pathname,
            "proc_info_pathname": proc_info_pathname,
        }
    )

    return dataframe


def query_products(
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
    Queries an ODC Database for both the test and reference products,
    then merges the results based on a common ancestor uuid.
    Assumes products have been indexed with lineage.

    :param product_name_test:
        Product name for the test datasets.

    :param product_name_reference:
        Product name for the reference datasets.

    :param db_env_test:
        Name of the database environment containing the test datasets.

    :param db_env_reference:
        Name of the database environment containing the reference
        datasets.

    :param time:
        The time (earliest, latest) extents (optional).

    :param lon:
        The longitude (left, right) extents (optional).

    :param lat:
        The latitude (top, bottom) extents (optional).

    :param additional_filters:
        A dictionary containing {field: value} pairs that datacube can
        use to further filter datasets.
        e.g. {"region_code": "092084"}
    """

    _LOG.info("querying the test datasets")
    test_dataframe = query_db(
        db_env_test, product_name_test, time, lon, lat, **additional_filters
    )

    _LOG.info("querying the reference datasets")
    reference_dataframe = query_db(
        db_env_reference, product_name_reference, time, lon, lat, **additional_filters
    )

    _LOG.info("filtering test and reference datasets for common ancestor")
    merged = pandas.merge(
        test_dataframe,
        reference_dataframe,
        on="uuid",
        how="inner",
        suffixes=["_test", "_reference"],
    )

    return merged


def query_filepath(path, pattern):
    """
    Find datasets by globbing the filesystem.

    :param path:
        The full pathname to the directory containing the product.

    :param pattern:
        A string containing pattern used to glob the filesystem.
        eg `*/*/2019/05/*/*.odc-metadata.yaml`
    """
    files = list(path.rglob(pattern))

    uuid = []
    yaml_pathname = []
    proc_info_pathname = []

    _LOG.info(
        "finding datasets", path=path, pattern=pattern,
    )

    for fname in files:
        _LOG.info("processing dataset", dataset=str(fname))

        doc = Digestyaml(fname)
        uuid.append(doc.parent_uuid)
        yaml_pathname.append(str(fname))

        # procssing info document
        pathname = fname.parent.joinpath(
            doc.doc["accessories"]["metadata:processor"]["path"]
        )
        proc_info_pathname.append(str(pathname))

    dataframe = pandas.DataFrame(
        {
            "level1_uuid": uuid,
            "yaml_pathname": yaml_pathname,
            "proc_info_pathname": proc_info_pathname,
        }
    )

    return dataframe


def query_via_filepath(
    test_directory, reference_directory, test_pattern, reference_pattern
):
    """
    Find the test and reference datasets by globbing the filesystem.

    :param test_directory:
        The full pathname to the directory containing the test product.

    :param reference_directory:
        The full pathname to the directory containing the reference product.

    :param test_pattern:
        A string containing pattern used to glob the filesystem.
        eg `*/*/2019/05/*/*.odc-metadata.yaml`

    :param reference_pattern:
        A string containing pattern used to glob the filesystem.
        eg `*/*/2019/05/*/*.odc-metadata.yaml`
    """

    test_dir = Path(test_directory)
    reference_dir = Path(reference_directory)

    _LOG.info("querying the test datasets")
    test_dataframe = query_filepath(test_dir, test_pattern)

    _LOG.info("querying the reference datasets")
    reference_dataframe = query_filepath(reference_dir, reference_pattern)

    _LOG.info("filtering test and reference datasets for common ancestor")
    merged = pandas.merge(
        test_dataframe,
        reference_dataframe,
        on="uuid",
        how="inner",
        suffixes=["_test", "_reference"],
    )

    return merged
