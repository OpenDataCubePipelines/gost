#!/usr/bin/env python

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.backends.backend_pdf import PdfPages
import geopandas


GDF = geopandas.read_file("raijin-gadi-C3-comparison.geojson")
RENAME_FIELDS = {
    "measurement": "Measurement",
    "minv": "MinResidual",
    "maxv": "MaxResidual",
    "percentile_90": "Percentile90",
    "percentile_99": "Percentile99",
    "percent_different": "PercentDifferent",
    "percent_data_2_null": "PercentData2Null",
    "percent_null_2_data": "PercentNull2Data",
}
GDF.rename(columns=RENAME_FIELDS, inplace=True)
COLS = [
    "MinResidual",
    "MaxResidual",
    "Percentile90",
    "Percentile99",
    "PercentDifferent",
    "PercentData2Null",
    "PercentNull2Data",
]
COLS2DIVIDE = [
    "MinResidual",
    "MaxResidual",
    "Percentile90",
    "Percentile99",
]
TM_GDF = geopandas.read_file("TM_WORLD_BORDERS_geodata100k.shp")
WRS2_GDF = geopandas.read_file("landsat_wrs2_descending.geojsonl")

LABELS = {
    "nbar_coastal_aerosol": "% Reflectance",
    "nbar_blue": "% Reflectance",
    "nbar_green": "% Reflectance",
    "nbar_red": "% Reflectance",
    "nbar_nir": "% Reflectance",
    "nbar_swir_1": "% Reflectance",
    "nbar_swir_2": "% Reflectance",
    "nbar_panchromatic": "% Reflectance",
    "nbart_coastal_aerosol": "% Reflectance",
    "nbart_blue": "% Reflectance",
    "nbart_green": "% Reflectance",
    "nbart_red": "% Reflectance",
    "nbart_nir": "% Reflectance",
    "nbart_swir_1": "% Reflectance",
    "nbart_swir_2": "% Reflectance",
    "nbart_panchromatic": "% Reflectance",
    "oa_azimuthal_exiting": "Degrees",
    "oa_azimuthal_incident": "Degrees",
    "oa_exiting_angle": "Degrees",
    "oa_incident_angle": "Degrees",
    "oa_relative_azimuth": "Degrees",
    "oa_relative_slope": "Slope",
    "oa_satellite_azimuth": "Degrees",
    "oa_satellite_view": "Degrees",
    "oa_solar_azimuth": "Degrees",
    "oa_solar_zenith": "Degrees",
    "oa_fmask": "Categorical",
    "oa_combined_terrain_shadow": "Categorical",
    "oa_nbar_contiguity": "Categorical",
    "oa_nbart_contiguity": "Categorical",
    "oa_time_delta": "Seconds",
}
LABELS2 = {
    "nbar_coastal_aerosol": "% Reflectance",
    "nbar_blue": "% Reflectance",
    "nbar_green": "% Reflectance",
    "nbar_red": "% Reflectance",
    "nbar_red_edge_1": "% Reflectance",
    "nbar_red_edge_2": "% Reflectance",
    "nbar_red_edge_3": "% Reflectance",
    "nbar_nir_1": "% Reflectance",
    "nbar_nir_2": "% Reflectance",
    "nbar_swir_2": "% Reflectance",
    "nbar_swir_3": "% Reflectance",
    "nbart_coastal_aerosol": "% Reflectance",
    "nbart_blue": "% Reflectance",
    "nbart_green": "% Reflectance",
    "nbart_red": "% Reflectance",
    "nbart_red_edge_1": "% Reflectance",
    "nbart_red_edge_2": "% Reflectance",
    "nbart_red_edge_3": "% Reflectance",
    "nbart_nir_1": "% Reflectance",
    "nbart_nir_2": "% Reflectance",
    "nbart_swir_2": "% Reflectance",
    "nbart_swir_3": "% Reflectance",
    "azimuthal_exiting": "Degrees",
    "azimuthal_incident": "Degrees",
    "exiting": "Degrees",
    "incident": "Degrees",
    "relative_azimuth": "Degrees",
    "relative_slope": "Slope",
    "satellite_azimuth": "Degrees",
    "satellite_view": "Degrees",
    "solar_azimuth": "Degrees",
    "solar_zenith": "Degrees",
    "fmask": "Categorical",
    "terrain_shadow": "Categorical",
    "nbar_contiguity": "Categorical",
    "nbart_contiguity": "Categorical",
    "timedelta": "Seconds",
}
SKIP = {
    "oa_relative_slope",
    "relative_slope",
    "oa_fmask",
    "fmask",
}


def plot_png(gdf, outdir):
    for name, grp in gdf.groupby("Measurement"):
        for col in COLS:
            prefix = Path(outdir, name.split('_')[0])
            if not prefix.exists():
                prefix.mkdir()

            out_fname = prefix.joinpath("{}-{}.png".format(name, col))
            fig, axes = plt.subplots()
            # fig = plt.figure(figsize=(3, 3), constrained_layout=True)
            #fig = plt.figure(figsize=(3, 3))
            #axes = fig.add_subplot()

            label = LABELS[name]

            grp.plot(column=col, cmap="rainbow", legend=False, ax=axes)

            if "%" in label:
                if col in COLS2DIVIDE:
                    # series = grp[col] / 100
                    series = grp[col]
                else:
                    series = grp[col]
                # series = grp[col] / 10000

                norm = colors.Normalize(vmin=series.min(), vmax=series.max())
                cbar = plt.cm.ScalarMappable(norm=norm, cmap='rainbow')

                ax_cbar = fig.colorbar(cbar, ax=axes)
                ax_cbar.set_label(label)

            TM_GDF.plot(linewidth=0.25, edgecolor="black",
                        facecolor="none", ax=axes)
            # axes.set_title("{} {}".format(name, col))
            axes.set_xlim(105, 160)
            axes.set_ylim(-45, -5)
            axes.set_xlabel("longitude")
            axes.set_ylabel("latitude")
            # axes.colorbar(title='% Reflectance (Scaled)')
            plt.savefig(out_fname, bbox_inches='tight')
            plt.close(fig)


def plot_png_s2(gdf, outdir):
    for name, grp in gdf.groupby("Measurement"):
        for col in COLS:
            prefix = Path(outdir, name.split('_')[0])
            if not prefix.exists():
                prefix.mkdir()

            out_fname = prefix.joinpath("{}-{}.png".format(name, col))
            # fig, axes = plt.subplots()
            # fig = plt.figure(figsize=(3, 3), constrained_layout=True)
            fig = plt.figure(figsize=(3, 3))
            axes = fig.add_subplot()

            label = LABELS2[name]

            grp.plot(column=col, cmap="rainbow", legend=False, ax=axes)

            if "%" in label:
                if col in COLS2DIVIDE:
                    # series = grp[col] / 100
                    series = grp[col]
                else:
                    series = grp[col]
                # series = grp[col] / 10000

                norm = colors.Normalize(vmin=series.min(), vmax=series.max())
                cbar = plt.cm.ScalarMappable(norm=norm, cmap='rainbow')

                ax_cbar = fig.colorbar(cbar, ax=axes)
                ax_cbar.set_label(label)

            TM_GDF.plot(linewidth=0.25, edgecolor="black",
                        facecolor="none", ax=axes)
            # axes.set_title("{} {}".format(name, col))
            axes.set_xlim(105, 160)
            axes.set_ylim(-45, -5)
            axes.set_xlabel("longitude")
            axes.set_ylabel("latitude")
            # axes.colorbar(title='% Reflectance (Scaled)')
            plt.savefig(out_fname, bbox_inches='tight')
            plt.close(fig)


def plot_pcts_png(gdf, outdir):
    for name, grp in gdf.groupby("Measurement"):
        for col in ['PercentDifferent']:
            prefix = Path(outdir, name.split('_')[0])
            if not prefix.exists():
                prefix.mkdir()

            out_fname = prefix.joinpath("{}-{}.png".format(name, col))
            # fig, axes = plt.subplots()
            # fig = plt.figure(figsize=(3, 3), constrained_layout=True)
            fig = plt.figure(figsize=(3, 3))
            axes = fig.add_subplot()

            label = "% of Pixels != 0"

            grp.plot(column=col, cmap="rainbow", legend=False, ax=axes)

            series = grp[col]
            norm = colors.Normalize(vmin=series.min(), vmax=series.max())
            cbar = plt.cm.ScalarMappable(norm=norm, cmap='rainbow')

            ax_cbar = fig.colorbar(cbar, ax=axes)
            ax_cbar.set_label(label)

            TM_GDF.plot(linewidth=0.25, edgecolor="black",
                        facecolor="none", ax=axes)
            # axes.set_title("{} {}".format(name, col))
            axes.set_xlim(105, 160)
            axes.set_ylim(-45, -5)
            axes.set_xlabel("longitude")
            axes.set_ylabel("latitude")
            # axes.colorbar(title='% Reflectance (Scaled)')
            plt.savefig(out_fname, bbox_inches='tight')
            plt.close(fig)
