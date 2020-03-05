#!/usr/bin/env python

"""
A temporary script that at least fleshes out some basic stats/tests
that might be useful.
Once a new direction has been sorted out, this and other accompanying
scripts will be designed and executed properly.
The goal is to be as sensor and collection generic as possible.
"""

from pathlib import Path
import click
import h5py
from mpi4py import MPI
import pandas
import structlog

from wagl.tiling import scatter
from wagl.hdf5 import write_dataframe

from compare_measurements import process_yamls
from eede0bc6ab557cf3d6084ba3b63e6c1c import mpi_logger as mlog


@click.command()
@click.option("--reference-dir", type=click.Path(file_okay=False,
              readable=True), help="The base reference directory.")
@click.option("--test-dir", type=click.Path(file_okay=False, readable=True),
              help="The base test directory.")
@click.option("--out-pathname", help="The pathname for the output file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--log-pathname", help="The pathname for the output log file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--pattern", type=click.STRING, required=True,
              help=("Pattern to use for a recursive glob search. "
                    "Examples include: *.odc-metadata.yaml, ga-metadata.yaml, "
                    "ARD-METADATA.yaml"))
def main(reference_dir, test_dir, out_pathname, log_pathname, pattern):
    # initialise the output stream for logging
    out_stream = mlog.MPIStreamIO(log_pathname)
    structlog.configure(
        processors=mlog.DEFAULT_PROCESSORS,
        logger_factory=mlog.MPILoggerFactory(out_stream)
    )

    log = structlog.get_logger()

    # comm info
    comm = MPI.COMM_WORLD

    # processor info
    rank = comm.Get_rank()
    n_proc = comm.Get_size()

    # directories we're working with
    test_dir = Path(test_dir)
    reference_dir = Path(reference_dir)
    out_pathname = Path(out_pathname)
    product_dir_name = test_dir.name

    if rank == 0:
        if not out_pathname.parent.exists():
            log.info('creating output directory')
            out_pathname.parent.mkdir()

    # locate yaml documents
    if rank == 0:
        yaml_fnames = list(test_dir.rglob(pattern))
        if not yaml_fnames:
            log.warning('no yaml docs found')
        blocks = scatter(yaml_fnames, n_proc)
    else:
        blocks = None

    yaml_fnames = comm.scatter(blocks, root=0)

    # check for existence
    # TODO; scatter existing list and find valid yamls, then collect
    valid_yamls = []
    for fname in yaml_fnames:
        path_parts = fname.parent.parts
        idx = path_parts.index(product_dir_name)
        sub_path = path_parts[idx:]
        ref_fname = reference_dir.joinpath(*sub_path, fname.name)
        if ref_fname.exists():
            valid_yamls.append(fname)
        else:
            log.warning("skipping document", reference_fname=ref_fname,
                        test_fname=fname)

    valid_yamls = comm.gather(valid_yamls, root=0)

    if rank == 0:
        valid_yamls = sum(valid_yamls, [])
        blocks = scatter(valid_yamls, n_proc)
    else:
        blocks = None

    comm.Barrier()

    # split work across all processors
    yaml_pathnames = comm.scatter(blocks, root=0)
    log.info('processing {} documents'.format(len(yaml_pathnames)))

    # process
    results = process_yamls(yaml_pathnames, reference_dir, product_dir_name)
    general_recs, fmask_recs, contiguity_recs, shadow_records = results

    # gather records from all workers
    general_records = comm.gather(results[0], root=0)
    fmask_records = comm.gather(results[1], root=0)
    contiguity_records = comm.gather(results[2], root=0)
    shadow_records = comm.gather(results[3], root=0)

    # create dataframes for each set of results
    if rank == 0:
        log.info('appending dataframes')
        if general_records:
            general_df = pandas.DataFrame(general_records[0])
            for record in general_records[1:]:
                general_df = general_df.append(pandas.DataFrame(record))

        if fmask_records:
            fmask_df = pandas.DataFrame(fmask_records[0])
            for record in fmask_records[1:]:
                fmask_df = fmask_df.append(pandas.DataFrame(record))

        if contiguity_records:
            contiguity_df = pandas.DataFrame(contiguity_records[0])
            for record in contiguity_records[1:]:
                contiguity_df = contiguity_df.append(pandas.DataFrame(record))

        if shadow_records:
            shadow_df = pandas.DataFrame(shadow_records[0])
            for record in shadow_records[1:]:
                shadow_df = shadow_df.append(pandas.DataFrame(record))

        # reset to a unique index
        log.info('reset dataframe index')
        if general_records:
            general_df.reset_index(drop=True, inplace=True)
        if fmask_records:
            fmask_df.reset_index(drop=True, inplace=True)
        if contiguity_records:
            contiguity_df.reset_index(drop=True, inplace=True)
        if shadow_records:
            shadow_df.reset_index(drop=True, inplace=True)

        # save each table
        log.info('saving dataframes to tables')
        with h5py.File(str(out_pathname), 'w') as fid:
            if general_records:
                write_dataframe(general_df, 'GENERAL-RESULTS', fid)
            if fmask_records:
                write_dataframe(fmask_df, 'FMASK-RESULTS', fid)
            if contiguity_records:
                write_dataframe(contiguity_df, 'CONTIGUITY-RESULTS', fid)
            if shadow_records:
                write_dataframe(shadow_df, 'SHADOW-RESULTS', fid)


if __name__ == '__main__':
    main()
