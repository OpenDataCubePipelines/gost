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


FUNCS = [numpy.min, numpy.max, numpy.mean]


def summarise_general_results(pathname, out_pathname):
    """Summarise the general results table"""
    gdf = geopandas.read_file(str(pathname))

    cols = ['minv', 'maxv', 'percent_different']

    # out_pathname = outdir.joinpath('summary-general-results.csv')
    pivot = pandas.pivot_table(gdf, index=['measurement'], values=cols,
                               aggfunc=FUNCS)

    # we're reshaping here simply to get a cleaner table structure to output
    pivot = pivot.transpose().unstack().transpose()

    pivot.to_csv(str(out_pathname))


def summarise_catgegorical_results(pathname, out_pathname):
    """Summarise a generic categorical table"""
    gdf = geopandas.read_file(str(pathname))

    # we are assuming columns of interest are of the format <field_2_field>
    cols = [i for i in gdf.columns if '_2_' in i]

    pivot = pandas.pivot_table(gdf, index=['measurement'], values=cols,
                               aggfunc=FUNCS)

    # we're reshaping here simply to get a cleaner table structure to output
    pivot = pivot.transpose().unstack().transpose()

    pivot.to_csv(str(out_pathname))


@click.command()
@click.option("--pathname",
              help="The pathname for the generak comparison input file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--out-pathname",
              help="The pathname for the summary output file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--categorical", default=False, is_flag=True,
              help="If set, the input file should contain categorical data")
def main(pathname, out_pathname, categorical):
    """Produce summary statistics for the wagl and Fmask outputs."""
    pathname = Path(pathname)
    out_pathname = Path(out_pathname)

    if not out_pathname.parent.exists():
        out_pathname.parent.mkdir()

    # summarise the table
    if categorical:
        summarise_catgegorical_results(pathname, out_pathname)
    else:
        summarise_general_results(pathname, out_pathname)


if __name__ == '__main__':
    main()
