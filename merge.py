#!/usr/bin/env python

"""
A temporary script that at least fleshes out some basic stats/tests
that might be useful.
Once a new direction has been sorted out, this and other accompanying
scripts will be designed and executed properly.
"""

from pathlib import Path
import click
import h5py
import pandas
import geopandas

from wagl.hdf5 import write_dataframe, read_h5_table

WRS2_FNAME = '/g/data/v10/testing_ground/jps547/wrs2-descending/wrs2_descending_v2.shp'


@click.command()
@click.option("--indir", type=click.Path(file_okay=False, readable=True),
              help="The base input directory.")
@click.option("--outdir", type=click.Path(file_okay=False, writable=True),
              help="The base output directory.")
def main(indir, outdir):

    indir = Path(indir)
    outdir = Path(outdir)

    if not outdir.exists():
        outdir.mkdir()

    # read each table
    fname = indir.joinpath('raijin-gadi-C3-comparison.h5')
    with h5py.File(str(fname), 'r') as fid:
        df = read_h5_table(fid, 'RESULTS')
        fmask_df = read_h5_table(fid, 'FMASK-RESULTS')

    # table merge based on region code
    wrs2_df = geopandas.read_file(WRS2_FNAME)
    new_df = pandas.merge(df, wrs2_df, how='left', left_on=['region_code'],
                          right_on=['RCODE'])
    new_fmask_df = pandas.merge(fmask_df, wrs2_df, how='left',
                                left_on=['region_code'], right_on=['RCODE'])

    # save geojson
    out_fname = outdir.joinpath('raijin-gadi-C3-comparison.geojson')
    gdf = geopandas.GeoDataFrame(new_df, crs=wrs2_df.crs)
    gdf.drop(labels=['AREA', 'PERIMETER', 'PR_', 'PR_ID', 'RINGS_OK', 'RINGS_NOK', 'WRSPR', 'PR', 'PATH', 'ROW', 'MODE', 'DAYCLASS', 'SEQUENCE', 'RCODE'], axis=1, inplace=True)
    gdf.to_file(str(out_fname), driver='GeoJSON')

    out_fname = outdir.joinpath('raijin-gadi-C3-fmask-comparison.geojson')
    gdf = geopandas.GeoDataFrame(new_fmask_df, crs=wrs2_df.crs)
    gdf.drop(labels=['AREA', 'PERIMETER', 'PR_', 'PR_ID', 'RINGS_OK', 'RINGS_NOK', 'WRSPR', 'PR', 'PATH', 'ROW', 'MODE', 'DAYCLASS', 'SEQUENCE', 'RCODE'], axis=1, inplace=True)
    gdf.to_file(str(out_fname), driver='GeoJSON')


if __name__ == '__main__':
    main()
