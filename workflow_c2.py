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

from wagl.tiling import scatter
from wagl.scripts.wagl_residuals import distribution
from wagl.hdf5 import write_dataframe

from utils import FmaskCategories, evaluate2, evaluate_fmask, evaluate_nulls, data_mask
# from mpi_logger import LOG


@click.command()
@click.option("--reference-dir", type=click.Path(file_okay=False,
              readable=True), help="The base reference directory.")
@click.option("--test-dir", type=click.Path(file_okay=False, readable=True),
              help="The base test directory.")
@click.option("--outdir", type=click.Path(file_okay=False, writable=True),
              help="The base output directory.")
def main(reference_dir, test_dir, outdir):
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

    if not outdir.exists():
        if rank == 0:
            outdir.mkdir()

    # locate yaml documents
    yaml_fnames = list(test_dir.rglob('ga-metadata.yaml'))

    # scatter work across processes
    fnames = scatter(yaml_fnames, n_proc)[rank]

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

    for fname in fnames:
        with open(fname) as src:
            doc = yaml.load(src)

        product = doc['product_type']
        path_parts = fname.parent.parts
        idx = path_parts.index(product)
        sub_path = path_parts[idx:]

        for band in doc['image']['bands']:
            tif_name = doc['image']['bands'][band]['path']
            test_fname = fname.parent.joinpath(tif_name)
            ref_fname = reference_dir.joinpath(*sub_path, tif_name)

            if not ref_fname.exists():
                continue

            ref_ds = rasterio.open(ref_fname)
            test_ds = rasterio.open(test_fname)

            # compute results
            # null data evaluation
            valid_2_null_pct, null_2_valid_pct = evaluate_nulls(ref_ds, test_ds)
            records['percent_data_2_null'].append(valid_2_null_pct)
            records['percent_null_2_data'].append(null_2_valid_pct)

            diff = evaluate2(ref_ds, test_ds)
            h = distribution(diff)

            # store results
            label = doc['ga_label']
            records['granule'].append(label)
            records['reference_fname'].append(str(ref_fname))
            records['test_fname'].append(str(test_fname))
            records['region_code'].append(''.join(label.split('_')[-3:-1]))
            records['size'].append(diff.size)
            records['measurement'].append(band)
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

    # create dataframes
    if rank == 0:
        df = pandas.DataFrame(appended_records[0])
        for record in appended_records[1:]:
            df = df.append(pandas.DataFrame(record))

        # reset to a unique index
        df.reset_index(drop=True, inplace=True)

        # save each table
        out_fname = outdir.joinpath('raijin-gadi-C3-comparison.h5')
        with h5py.File(str(out_fname), 'w') as fid:
            write_dataframe(df, 'RESULTS', fid)


if __name__ == '__main__':
    main()
