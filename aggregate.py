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
import pandas
import geopandas


def aggregate_general_results(pathname, outdir):
    """Aggregate the general results table"""
    gdf = geopandas.read_file(str(pathname))

    out_pathname = outdir.joinpath('min-aggregate-general-results-minmax.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=['minv', 'maxv'], aggfunc=numpy.min)
    pivot.to_csv(str(out_pathname))

    out_pathname = outdir.joinpath('max-aggregate-general-results-minmax.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=['minv', 'maxv'], aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    fname = 'max-aggregate-general-results-percent-different.csv'
    out_pathname = outdir.joinpath(fname)
    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=['percent_different'], aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))


def aggregate_fmask_results(pathname, outdir):
    """Aggregate the fmask results table"""
    gdf = geopandas.read_file(str(pathname))

    null = [i for i in gdf.columns if 'null_2' in i]
    clear = [i for i in gdf.columns if 'clear_2' in i]
    cloud = [i for i in gdf.columns if 'cloud_2' in i]
    shadow = [i for i in gdf.columns if 'shadow_2' in i]
    snow = [i for i in gdf.columns if 'snow_2' in i]
    water = [i for i in gdf.columns if 'water_2' in i]

    out_pathname = outdir.joinpath('max-aggregate-fmask-results-null.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=null,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    out_pathname = outdir.joinpath('max-aggregate-fmask-results-clear.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=clear,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    out_pathname = outdir.joinpath('max-aggregate-fmask-results-cloud.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=cloud,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    out_pathname = outdir.joinpath('max-aggregate-fmask-results-shadow.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=shadow,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    out_pathname = outdir.joinpath('max-aggregate-fmask-results-snow.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=snow,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    out_pathname = outdir.joinpath('max-aggregate-fmask-results-water.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=water,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))


def aggregate_contiguity_results(pathname, outdir):
    """Aggregate the contiguity results table"""
    gdf = geopandas.read_file(str(pathname))

    non_contiguous = [i for i in gdf.columns if 'non_contiguous_2' in i]
    contiguous = [i for i in gdf.columns if 'contiguous_2' in i]

    fname = 'max-aggregate-contiguity-results-non-contiguous.csv'
    out_pathname = outdir.joinpath(fname)
    pivot = pandas.pivot_table(gdf, index=['measurement'],
                               values=non_contiguous,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    fname = 'max-aggregate-contiguity-results-contiguity.csv'
    out_pathname = outdir.joinpath(fname)
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=contiguous,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))


def aggregate_shadow_results(pathname, outdir):
    """Aggregate the terrain shadow results table"""
    gdf = geopandas.read_file(str(pathname))

    shadow = [i for i in gdf.columns if 'shaded_2' in i]
    unshaded = [i for i in gdf.columns if 'unshaded_2' in i]

    fname = 'max-aggregate-terrain-shadow-results-shadow.csv'
    out_pathname = outdir.joinpath(fname)
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=shadow,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))

    fname = 'max-aggregate-terrain-shadow-results-unshaded.csv'
    out_pathname = outdir.joinpath(fname)
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=unshaded,
                               aggfunc=numpy.max)
    pivot.to_csv(str(out_pathname))


@click.command()
@click.option("--pathname1",
              help="The pathname for the generak comparison input file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--pathname2",
              help="The pathname for the fmask comparison input file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--pathname3",
              help="The pathname for the contiguity comparison input file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--pathname4",
              help="The pathname for the shadow comparison input file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--outdir", type=click.Path(file_okay=False, writable=True),
              help=("The base output directory to contain the summarised "
                    "statistics."))
def main(pathname1, pathname2, pathname3, pathname4, outdir):
    """Produce summary statistics for the wagl and Fmask outputs."""
    pathname1 = Path(pathname1)
    pathname2 = Path(pathname2)
    pathname3 = Path(pathname3)
    pathname4 = Path(pathname4)
    outdir = Path(outdir)

    if not outdir.exists():
        outdir.mkdir()

    # aggregate each component
    aggregate_general_results(pathname1, outdir)
    aggregate_fmask_results(pathname2, outdir)
    aggregate_contiguity_results(pathname3, outdir)
    aggregate_shadow_results(pathname4, outdir)


if __name__ == '__main__':
    main()
