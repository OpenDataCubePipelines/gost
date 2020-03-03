#!/usr/bin/env python

"""
A temporary script that at least fleshes out some basic stats/tests
that might be useful.
Once a new direction has been sorted out, this and other accompanying
scripts will be designed and executed properly.
"""

from pathlib import Path
import click
import numpy
import h5py
from mpi4py import MPI
import yaml
import pandas
import rasterio
import structlog

from wagl.tiling import scatter
from wagl.scripts.wagl_residuals import distribution
from wagl.hdf5 import write_dataframe

from digest_yaml import Digestyaml
from utils import FmaskCategories, evaluate2, evaluate_fmask, evaluate_nulls, data_mask
from eede0bc6ab557cf3d6084ba3b63e6c1c import mpi_logger as mlog


@click.command()
@click.option("--reference-dir", type=click.Path(file_okay=False,
              readable=True), help="The base reference directory.")
@click.option("--test-dir", type=click.Path(file_okay=False, readable=True),
              help="The base test directory.")
@click.option("--outdir", type=click.Path(file_okay=False, writable=True),
              help="The base output directory.")
def main(reference_dir, test_dir, outdir):
    product = 'S2_MSI_ARD'

    # initialise the output stream for logging
    out_stream = mlog.MPIStreamIO('status.log')
    structlog.configure(
        processors=mlog.DEFAULT_PROCESSORS,
        logger_factor=mlog.MPILoggerFactory(out_stream)
    )

    log = structlog.get_logger()
    # log = LOG.bind()

    # comm info
    comm = MPI.COMM_WORLD

    # processor info
    # rank = MPI.COMM_WORLD.rank
    # n_proc = MPI.COMM_WORLD.size
    rank = comm.Get_rank()
    n_proc = comm.Get_size()

    # directories we're working with
    test_dir = Path(test_dir)
    reference_dir = Path(reference_dir)
    outdir = Path(outdir)

    product_dir_name = reference_dir.name

    if rank == 0:
        if not outdir.exists():
            log.info('creating output directory')
            outdir.mkdir()

    # locate yaml documents
    if rank == 0:
        yaml_fnames = list(test_dir.rglob('ARD-METADATA.yaml'))
        if not yaml_fnames:
            log.warning('no yaml docs found')

        # check for existence
        valid_yamls = []
        for fname in yaml_fnames:
            path_parts = fname.parent.parts
            idx = path_parts.index(product_dir_name)
            sub_path = path_parts[idx:]
            ref_fname = reference_dir.joinpath(*sub_path, fname.name)
            if ref_fname.exists():
                valid_yamls.append(fname)
            else:
                log.warning("skipping", reference_fname=ref_fname, test_fname=fname)

        blocks = scatter(valid_yamls, n_proc)
    else:
        blocks = None

    comm.Barrier()

    # split work across all processors
    fnames = comm.scatter(blocks, root=0)
    log.info('processing {} documents'.format(len(fnames)))

    # results
    records = {
        'granule': [],
        'reference_fname': [],
        'test_fname': [],
        'measurement': [],
        'minv': [],
        'maxv': [],
        'percent_different': [],
        'percentile_90': [],
        'percentile_99': [],
        'percent_data_2_null': [],
        'percent_null_2_data': [],
        'size': [],
        'region_code': [],
    }

    # fmask results (this is a crappy way to setup the output ...)
    # but this is a temp job to get something going
    fmask_records = {
        'granule': [],
        'reference_fname': [],
        'test_fname': [],
        'measurement': [],
        'size': [],
        'region_code': [],
    }
    for category in FmaskCategories:
        fmt = '{}_2_{}'
        for category2 in FmaskCategories:
            key = fmt.format(category.name.lower(), category2.name.lower())
            fmask_records[key] = []

    for fname in fnames:
        doc = Digestyaml(fname)

        path_parts = fname.parent.parts
        idx = path_parts.index(product_dir_name)
        sub_path = path_parts[idx:]

        for meas in doc.measurements:
            tif_name = doc.measurements[meas]['path']
            test_fname = fname.parent.joinpath(tif_name)
            ref_fname = reference_dir.joinpath(*sub_path, tif_name)

            if not ref_fname.exists():
                log.info('reference measurement not found', reference_measurement=ref_fname, test_measurement=test_fname)
                continue

            ref_ds = rasterio.open(ref_fname)
            test_ds = rasterio.open(test_fname)

            # compute results
            if meas in ['oa_fmask', 'fmask']:
                # the idea here is to analyse the categorical data differently
                fmask_records['granule'].append(doc.granule)
                fmask_records['region_code'].append(doc.region_code)
                fmask_records['reference_fname'].append(str(ref_fname))
                fmask_records['test_fname'].append(str(test_fname))
                fmask_records['size'].append(numpy.prod(ref_ds.shape))
                fmask_records['measurement'].append(meas)
                fmask_results = evaluate_fmask(ref_ds, test_ds)
                for key in fmask_results:
                    fmask_records[key].append(fmask_results[key])
            else:
                # null data evaluation
                valid_2_null_pct, null_2_valid_pct = evaluate_nulls(ref_ds, test_ds)
                records['percent_data_2_null'].append(valid_2_null_pct)
                records['percent_null_2_data'].append(null_2_valid_pct)

                diff = evaluate2(ref_ds, test_ds)
                h = distribution(diff)

                # store results
                records['granule'].append(doc.granule)
                records['reference_fname'].append(str(ref_fname))
                records['test_fname'].append(str(test_fname))
                records['region_code'].append(doc.region_code)
                records['size'].append(diff.size)
                records['measurement'].append(meas)
                records['minv'].append(h['omin'] / 100)
                records['maxv'].append(h['omax'] / 100)
                records['percent_different'].append(
                    (diff != 0).sum() / diff.size * 100
                )

                # percentiles of the cumulative distribution
                h = distribution(numpy.abs(diff))
                hist = h['histogram']
                cdf = numpy.cumsum(hist / hist.sum())
                p1_idx = numpy.searchsorted(cdf, 0.9)
                p2_idx = numpy.searchsorted(cdf, 0.99)

                # percentiles from cumulative distribution
                records['percentile_90'].append(h['loc'][p1_idx])
                records['percentile_99'].append(h['loc'][p2_idx])

    # gather records from all workers
    appended_records = comm.gather(records, root=0)
    appended_fmask_records = comm.gather(fmask_records, root=0)

    # create dataframes
    if rank == 0:
        log.info('appending dataframes')
        df = pandas.DataFrame(appended_records[0])
        for record in appended_records[1:]:
            df = df.append(pandas.DataFrame(record))

        fmask_df = pandas.DataFrame(appended_fmask_records[0])
        for record in appended_fmask_records[1:]:
            fmask_df = fmask_df.append(pandas.DataFrame(record))

        # reset to a unique index
        log.info('reset dataframe index')
        df.reset_index(drop=True, inplace=True)
        fmask_df.reset_index(drop=True, inplace=True)

        # save each table
        log.info('saving dataframes to tables')
        out_fname = outdir.joinpath('raijin-gadi-C3-comparison.h5')
        with h5py.File(str(out_fname), 'w') as fid:
            write_dataframe(df, 'RESULTS', fid)
            write_dataframe(fmask_df, 'FMASK-RESULTS', fid)


if __name__ == '__main__':
    main()
