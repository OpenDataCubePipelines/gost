import os
import re
import subprocess

from pathlib import Path
import click
import structlog
import datacube

from gost.constants import DirectoryNames
from ._shared_commands import io_dir_options, db_query_options

_LOG = structlog.get_logger()

PBS_RESOURCES = """#!/bin/bash
#PBS -P {project}
#PBS -W umask=017
#PBS -q normal
#PBS -l walltime={walltime},mem={memory}GB,ncpus={ncpus}
#PBS -l wd
#PBS -l storage={filesystem_projects}
#PBS -me
{email}

source {env}

"""
QUERY_CMD = """{resources}
ard-intercomparison query --outdir {outdir} --product-name-test {product_name_test} product-name-reference {product_name_reference} --db-env-test {db_env_test} --db-env-reference {db_env_reference} --time {time_from} {time_to}
"""
QUERY_FS_CMD = """{resources}
ard-intercomparison query-filesystem --outdir {outdir} --product-pathname-test {product_pathname_test} --product-pathname-reference {product_pathname_reference} --glob-pattern-test "{glob_pattern_test}" --glob-pattern-reference "{glob_pattern_reference}"
"""
COMPARISON_CMD = """{resources}
mpiexec -n {ncpus} ard-intercomparison comparison --outdir {outdir}
"""
GQA_COMPARISON_CMD = """{resources}
mpiexec -n {ncpus} ard-intercomparison comparison --outdir {outdir} --gqa
"""
COLLATE_CMD = """{resources}
ard-intercomparison collate --outdir {outdir}
"""
PLOTTING_CMD = """{resources}
ard-intercomparison plotting --outdir {outdir}
"""

LONGITUDE_OPT = "--lon {lon1} {lon2}"
LATITUDE_OPT = "--lat {lat1} {lat2}"
ADDITIONAL = "--additional-filters {additional_filters}"
FS_PROJECT_FMT = "scratch/{f_project}+gdata/{f_project}"
QSUB_DEPENDENCY = "#PBS -W depend=afterany:{jobid}"


def _qsub(job_string, out_fname, dependency=None):
    """Essentially writes and calls qsub."""

    out_fname = Path(out_fname)

    if not out_fname.parent.exists():
        out_fname.parent.mkdir(parents=True)

    _LOG.info("writing pbs job to disk", out_fname=str(out_fname))
    with open(out_fname, "w") as src:
        src.write(job_string)

    cmd = ["qsub"]
    if dependency:
        if isinstance(dependency, tuple):
            job_dependency = ":".join(dependency)
        else:
            job_dependency = dependency
        cmd.extend(["-W", "depend=afterok:{}".format(job_dependency)])

    cmd.append(out_fname.name)

    os.chdir(out_fname.parent)
    try:
        raw_output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as exc:
        _LOG.error("qsub failed with exit code %s", str(exc.returncode))
        _LOG.error(exc.output)
        raise

    if hasattr(raw_output, "decode"):
        matches = re.match(
            r"^(?P<nci_job_id>\d+\.gadi-pbs)$", raw_output.decode("utf-8")
        )
        if matches:
            nci_job_id = matches.groupdict()["nci_job_id"].split(".")[0]
        else:
            nci_job_id = None

    return nci_job_id


def _ncpus_memory(length, loading=3, node_cpus=48, node_memory=192):
    """Determine the number of cpus for the MPI job."""

    n_nodes = length // loading // node_cpus
    if n_nodes == 0:
        n_nodes = 1

    n_cpus = n_nodes * node_cpus
    memory = n_nodes * node_memory

    if n_cpus > length:
        n_cpus = length
        memory = (node_memory / node_cpus) * n_cpus

    return int(n_cpus), int(memory)


def _initial_query(
    product_name_test,
    db_env_test,
    time,
    lon,
    lat,
    additional_filters,
    query_filesystem,
):
    """
    Initial listing to see how many datasets we'll (at most) have to compare.
    """

    if query_filesystem:
        _LOG.info("filesystem queries can take a while, please be patient")

        path = Path(product_name_test)
        pattern = db_env_test

        _LOG.info("initial filesystem query", path=str(path), pattern=pattern)

        n_datasets = len(list(path.rglob(pattern)))
    else:
        dc = datacube.Datacube(env=db_env_test)

        _LOG.info(
            "initial database query",
            product=product_name_test,
            time=time,
            lon=lon,
            lat=lat,
        )

        n_datasets = len(
            dc.find_products(
                product_name_test, time=time, lon=lon, lat=lat, **additional_filters
            )
        )

    return n_datasets


def _setup_query_db_pbs_job(
    project,
    filesystem_projects,
    email_construct,
    env,
    outdir,
    product_name_test,
    product_name_reference,
    db_env_test,
    db_env_reference,
    time,
    lon=None,
    lat=None,
    additional_filters=None,
):
    """Setup and submit the PBS job for querying the required data."""
    query_resources = PBS_RESOURCES.format(
        project=project,
        walltime="00:15:00",
        memory=4,
        ncpus=1,
        filesystem_projects=filesystem_projects,
        email=email_construct,
        env=env,
    )

    query_pbs_job = QUERY_CMD.format(
        resources=query_resources,
        outdir=outdir,
        product_name_test=product_name_test,
        product_name_reference=product_name_reference,
        db_env_test=db_env_test,
        db_env_reference=db_env_reference,
        time_from=time[0],
        time_to=time[1],
    )

    # optional commands
    if lon:
        query_pbs_job = query_pbs_job + LONGITUDE_OPT.format(lon1=lon[0], lon2=lon[1])
    if lat:
        query_pbs_job = query_pbs_job + LATITUDE_OPT.format(lat1=lat[0], lat2=lat[1])
    if additional_filters:
        query_pbs_job = query_pbs_job + ADDITIONAL.format(additional=additional_filters)

    out_fname = Path(outdir).joinpath(
        DirectoryNames.PBS.value, "ard-intercomparison-query.bash"
    )

    nci_job_id = _qsub(query_pbs_job, out_fname)

    return nci_job_id


def _setup_query_filesystem_pbs_job(
    project,
    filesystem_projects,
    email_construct,
    env,
    outdir,
    product_pathname_test,
    product_pathname_reference,
    glob_pattern_test,
    glob_pattern_reference,
):
    """
    Setup and submit the PBS job for querying the filesystem for the
    required data.
    """

    query_resources = PBS_RESOURCES.format(
        project=project,
        walltime="00:15:00",
        memory=4,
        ncpus=1,
        filesystem_projects=filesystem_projects,
        email=email_construct,
        env=env,
    )

    query_pbs_job = QUERY_FS_CMD.format(
        resources=query_resources,
        outdir=outdir,
        product_pathname_test=product_pathname_test,
        product_pathname_reference=product_pathname_reference,
        glob_pattern_test=glob_pattern_test,
        glob_pattern_reference=glob_pattern_reference,
    )

    out_fname = Path(outdir).joinpath(
        DirectoryNames.PBS.value, "ard-intercomparison-query.bash"
    )

    nci_job_id = _qsub(query_pbs_job, out_fname)

    return nci_job_id


def _setup_comparison_pbs_job(
    n_datasets,
    dependency_jobid,
    project,
    filesystem_projects,
    email_construct,
    env,
    outdir,
):
    """
    Setup and submit the PBS jobs for comparing the test and reference data.
    Two jobs are submitted:
    * product measurement comparison
    * gqa fields comparison
    """

    n_cpus, memory = _ncpus_memory(n_datasets)
    comparison_resources = PBS_RESOURCES.format(
        project=project,
        walltime="00:45:00",
        memory=memory,
        ncpus=n_cpus,
        filesystem_projects=filesystem_projects,
        email=email_construct,
        env=env,
    )

    # product measurement comparison job
    measurement_pbs_job = COMPARISON_CMD.format(
        resources=comparison_resources, ncpus=n_cpus, outdir=outdir
    )

    out_fname = Path(outdir).joinpath(
        DirectoryNames.PBS.value, "ard-intercomparison-measurement-comparison.bash"
    )

    _LOG.info("submitting product measurement comparison pbs job")
    measurement_job_id = _qsub(measurement_pbs_job, out_fname, dependency_jobid)

    # gqa fields comparison job
    gqa_pbs_job = GQA_COMPARISON_CMD.format(
        resources=comparison_resources, ncpus=n_cpus, outdir=outdir
    )

    out_fname = Path(outdir).joinpath(
        DirectoryNames.PBS.value, "ard-intercomparison-gqa-comparison.bash"
    )

    _LOG.info("submitting product measurement comparison pbs job")
    gqa_job_id = _qsub(gqa_pbs_job, out_fname, dependency_jobid)

    return measurement_job_id, gqa_job_id


def _setup_collate_pbs_job(
    dependency_jobids, project, filesystem_projects, email_construct, env, outdir,
):
    """Setup and submit the PBS job for collating the results of the comparison."""

    collate_resources = PBS_RESOURCES.format(
        project=project,
        walltime="00:15:00",
        memory=4,
        ncpus=1,
        filesystem_projects=filesystem_projects,
        email=email_construct,
        env=env,
    )

    collate_pbs_job = COLLATE_CMD.format(resources=collate_resources, outdir=outdir)

    out_fname = Path(outdir).joinpath(
        DirectoryNames.PBS.value, "ard-intercomparison-collate.bash"
    )
    nci_job_id = _qsub(collate_pbs_job, out_fname, dependency_jobids)

    return nci_job_id


def _setup_plotting_pbs_job(
    dependency_jobid, project, filesystem_projects, email_construct, env, outdir,
):
    """Setup and submit the PBS job for plotting the results of the comparison."""

    plotting_resources = PBS_RESOURCES.format(
        project=project,
        walltime="00:45:00",
        memory=4,
        ncpus=1,
        filesystem_projects=filesystem_projects,
        email=email_construct,
        env=env,
    )

    plotting_pbs_job = PLOTTING_CMD.format(resources=plotting_resources, outdir=outdir)

    out_fname = Path(outdir).joinpath(
        DirectoryNames.PBS.value, "ard-intercomparison-plotting.bash"
    )
    nci_job_id = _qsub(plotting_pbs_job, out_fname, dependency_jobid)

    return nci_job_id


@click.command()
@io_dir_options
@click.option(
    "--env",
    type=click.Path(exists=True, readable=True),
    help="Environment script to source.",
)
@click.option(
    "--project",
    type=click.STRING,
    required=True,
    help="Project code to allocate the compute costs.",
)
@click.option(
    "--filesystem-projects",
    "-fsp",
    multiple=True,
    default=["v10", "xu18", "up71", "u46", "r78", "fj7", "da82"],
    help="Required filesystem projects.",
)
@click.option(
    "--email", type=click.STRING, default="", help="Notification email address."
)
@db_query_options
@click.option(
    "--query-filesystem",
    default=False,
    is_flag=True,
    help=(
        "If set, then instead of querying an ODC database, we query the "
        "filesystem instead. "
        "The commands product-name-test and --product-name-reference "
        "are used to specify the directory pathnames to the test and reference products. "
        "eg '/g/data/xu18/ga/ga_ls8c_ard_3'. "
        "The commands --db-env-test and --db-env-reference are used to "
        "specify the glob pattern to search, "
        "eg '*/*/2019/05/*/*.odc-metadata.yaml'."
    ),
)
def pbs(
    outdir,
    env,
    project,
    filesystem_projects,
    email,
    product_name_test,
    product_name_reference,
    db_env_test,
    db_env_reference,
    time,
    lon,
    lat,
    additional_filters,
    query_filesystem,
):
    """
    Product intercomparison PBS workflow.
    """

    email_construct = ("#PBS -M " + email) if email else ""
    fs_projects = "+".join(
        [FS_PROJECT_FMT.format(f_project=f) for f in filesystem_projects]
    )

    # an initial listing to see how many datasets we'll (at most) have to compare
    n_datasets = _initial_query(
        product_name_test,
        db_env_test,
        time,
        lon,
        lat,
        additional_filters,
        query_filesystem,
    )

    # query job
    if query_filesystem:
        _LOG.info("submitting query filesystem pbs job.")
        query_job_id = _setup_query_filesystem_pbs_job(
            project,
            fs_projects,
            email_construct,
            env,
            outdir,
            product_name_test,
            product_name_reference,
            db_env_test,
            db_env_reference,
        )
    else:
        _LOG.info("submitting query database pbs job")
        query_job_id = _setup_query_db_pbs_job(
            project,
            fs_projects,
            email_construct,
            env,
            outdir,
            product_name_test,
            product_name_reference,
            db_env_test,
            db_env_reference,
            time,
            lon,
            lat,
            additional_filters,
        )

    # intercomparison job
    _LOG.info("submitting comparison pbs jobs")
    comparison_job_ids = _setup_comparison_pbs_job(
        n_datasets, query_job_id, project, fs_projects, email_construct, env, outdir
    )

    # collate job
    _LOG.info("submitting collate pbs job")
    collate_job_id = _setup_collate_pbs_job(
        comparison_job_ids, project, fs_projects, email_construct, env, outdir
    )

    # plotting job
    _LOG.info("submitting plotting pbs job")
    plotting_job_id = _setup_plotting_pbs_job(
        collate_job_id, project, fs_projects, email_construct, env, outdir
    )

    _LOG.info(
        "submitted PBS jobs",
        query_job=query_job_id,
        product_measurement_comparison_job=comparison_job_ids[0],
        gqa_field_comparison_job=comparison_job_ids[1],
        collate_job=collate_job_id,
        plotting_job=plotting_job_id,
    )
