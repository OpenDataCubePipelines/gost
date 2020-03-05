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
@click.option("--out-pathname",
              help="The pathname for the comparison output file.",
              type=click.Path(file_okay=True, dir_okay=False))
@click.option("--framing", help="The grid framing definition to use.",
              type=click.Choice(["WRS2", "MGRS"]))
@click.option("--dataset-name",
              help="The dataset name to access from the input HDF5 file.")
def main(pathname, out_pathname, framing, dataset_name):
    """
    Output files will be created as GeoJSONSeq (JSONLines).
    As such, a filename extension of .geojsonl should be used.
    """

    pathname = Path(pathname)
    out_pathname = Path(out_pathname)
    framing_pathname = FRAMING[framing]

    if not out_pathname.parent.exists():
        out_pathname.parent.mkdir()

    # read each table
    with h5py.File(str(pathname), 'r') as fid:
        df = read_h5_table(fid, dataset_name)

    # table merge based on region code
    framing_df = geopandas.read_file(framing_pathname)
    new_df = pandas.merge(df, framing_df, how='left', left_on=['region_code'],
                          right_on=['region_code'])

    # save geojson
    gdf = geopandas.GeoDataFrame(new_df, crs=framing_df.crs)
    gdf.to_file(str(out_pathname), driver='GeoJSONSeq')


if __name__ == '__main__':
    main()
