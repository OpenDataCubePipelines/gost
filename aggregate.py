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
import pandas
import geopandas

from wagl.hdf5 import write_dataframe, read_h5_table


@click.command()
@click.option("--indir", type=click.Path(file_okay=False, readable=True),
              help="The base input directory.")
@click.option("--outdir", type=click.Path(file_okay=False, writable=True),
              help="The base output directory.")
def main(indir, outdir):
    """Do some quick summary stats."""
    indir = Path(indir)
    outdir = Path(outdir)

    if not outdir.exists():
        outdir.mkdir()

    fname = indir.joinpath('raijin-gadi-C3-comparison.geojson')
    gdf = geopandas.read_file(str(fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=['minv', 'maxv'], aggfunc=numpy.min)
    out_fname = outdir.joinpath('min-aggregate-results-minmax.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=['minv', 'maxv'], aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-results-minmax.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=['percent_different'], aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-results-percent-different.csv')
    pivot.to_csv(str(out_fname))

    fname = indir.joinpath('raijin-gadi-C3-fmask-comparison.geojson')
    gdf = geopandas.read_file(str(fname))

    null = [i for i in gdf.columns if 'null_2' in i]
    clear = [i for i in gdf.columns if 'clear_2' in i]
    cloud = [i for i in gdf.columns if 'cloud_2' in i]
    shadow = [i for i in gdf.columns if 'shadow_2' in i]
    snow = [i for i in gdf.columns if 'snow_2' in i]
    water = [i for i in gdf.columns if 'water_2' in i]

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=null,
                               aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-fmask-results-null.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=clear,
                               aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-fmask-results-clear.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=cloud,
                               aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-fmask-results-cloud.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=shadow,
                               aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-fmask-results-shadow.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=snow,
                               aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-fmask-results-snow.csv')
    pivot.to_csv(str(out_fname))

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=water,
                               aggfunc=numpy.max)
    out_fname = outdir.joinpath('max-aggregate-fmask-results-water.csv')
    pivot.to_csv(str(out_fname))


if __name__ == '__main__':
    main()
