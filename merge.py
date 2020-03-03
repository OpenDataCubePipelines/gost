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

WRS2_FNAME = "/g/data/v10/eoancillarydata-2/framing/landsat/landsat_wrs2_descending.geojsonl"
MGRS_FNAME = "/g/data/v10/eoancillarydata-2/framing/sentinel/sentinel-2-mgrs.geojsonl"
FRAMING = {
    "WRS2": WRS2_FNAME,
    "MGRS": MGRS_FNAME,
}


@click.command()
@click.option("--pathname", help="The pathname of the input file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--outdir", type=click.Path(file_okay=False, writable=True),
              help="The base output directory.")
@click.option("--out-pathname1",
              help="The pathname for the wagl comparison output file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--out-pathname2",
              help="The pathname for the fmask comparison output file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--framing", help="The grid framing definition to use.",
              type=click.Choice(["WRS2", "MGRS"]))
def main(pathname, out_pathname1, out_pathname2, framing):
    """
    Output files will be created as GeoJSONSeq (JSONLines).
    As such, a filename extension of .geojsonl should be used.
    """

    pathname = Path(pathname)
    out_pathname1 = Path(out_pathname1)
    out_pathname2 = Path(out_pathname2)
    framing_pathname = FRAMING[framing]

    if not out_pathname1.parent.exists():
        out_pathname1.parent.mkdir()

    if not out_pathname2.parent.exists():
        out_pathname1.parent.mkdir()

    # read each table
    with h5py.File(str(pathname), 'r') as fid:
        df = read_h5_table(fid, 'WAGL-RESULTS')
        fmask_df = read_h5_table(fid, 'FMASK-RESULTS')

    # table merge based on region code
    framing_df = geopandas.read_file(framing_pathname)
    new_df = pandas.merge(df, framing_df, how='left', left_on=['region_code'],
                          right_on=['region_code'])
    new_fmask_df = pandas.merge(fmask_df, framing_df, how='left',
                                left_on=['region_code'],
                                right_on=['region_code'])

    # save geojson
    gdf = geopandas.GeoDataFrame(new_df, crs=framing_df.crs)
    gdf.to_file(str(out_pathname1), driver='GeoJSONSeq')

    gdf = geopandas.GeoDataFrame(new_fmask_df, crs=framing_df.crs)
    gdf.to_file(str(out_pathname2), driver='GeoJSONSeq')


if __name__ == '__main__':
    main()
