#!/usr/bin/env python

from pathlib import Path
import numpy
import rasterio
import structlog

from wagl.scripts.wagl_residuals import distribution

from utils import ContiguityCategories, FmaskCategories
from utils import TerrainShadowCategories, GeneralRecords
from utils import FmaskRecords, TerrainShadowRecords, ContiguityRecords
from utils import evaluate2, evaluate_nulls, evaluate_categories
from digest_yaml import Digestyaml


BAND_IDS = ['1', '2', '3', '4', '5', '6', '7']
CONTIGUITY_MEASUREMENT_NAMES = [
    'oa_nbar_contiguity',
    'oa_nbart_contiguity',
    'nbar_contiguity',
    'nbart_contiguity'
]
SHADOW_MEASUREMENT_NAMES = [
    'oa_combined_terrain_shadow',
    'terrain_shadow'
]
FMASK_MEASUREMENT_NAMES = [
    'oa_fmask',
    'fmask'
]
LOG = structlog.get_logger()


def process_yamls(yaml_pathnames, reference_dir, product_dir_name):
    reference_dir = Path(reference_dir)

    # initialise placeholders for the results
    general_records = GeneralRecords()
    fmask_records = FmaskRecords()
    contiguity_records = ContiguityRecords()
    shadow_records = TerrainShadowRecords()

    for pathname in yaml_pathnames:
        LOG.info('processing document', yaml_doc=str(pathname.name))

        doc = Digestyaml(pathname)

        path_parts = pathname.parent.parts
        idx = path_parts.index(product_dir_name)
        sub_path = path_parts[idx:]

        for meas in doc.measurements:
            LOG.info(
                'processing measurement',
                measurement=meas,
                yaml_doc=str(pathname.name)
            )

            tif_name = doc.measurements[meas]['path']
            test_fname = pathname.parent.joinpath(tif_name)
            ref_fname = reference_dir.joinpath(*sub_path, tif_name)

            if not ref_fname.exists():
                LOG.info(
                    'missing reference measurement',
                    ref_measurement=ref_fname,
                    test_measurement=test_fname
                )
                continue

            ref_ds = rasterio.open(ref_fname)
            test_ds = rasterio.open(test_fname)

            # compute results
            if meas in FMASK_MEASUREMENT_NAMES:
                # the idea here is to analyse the categorical data differently
                fmask_records.granule.append(doc.granule)
                fmask_records.region_code.append(doc.region_code)
                fmask_records.reference_fname.append(str(ref_fname))
                fmask_records.test_fname.append(str(test_fname))
                fmask_records.size.append(numpy.prod(ref_ds.shape))
                fmask_records.measurement.append(meas)

                # categorical evaluation
                fmask_results = evaluate_categories(
                    ref_ds,
                    test_ds,
                    FmaskCategories
                )
                for key in fmask_results:
                    value = fmask_results[key]
                    getattr(fmask_records, key).append(value)
            elif meas in CONTIGUITY_MEASUREMENT_NAMES:
                # base records
                contiguity_records.granule.append(doc.granule)
                contiguity_records.region_code.append(doc.region_code)
                contiguity_records.reference_fname.append(str(ref_fname))
                contiguity_records.test_fname.append(str(test_fname))
                contiguity_records.size.append(numpy.prod(ref_ds.shape))
                contiguity_records.measurement.append(meas)

                # categorical evaluation
                contiguity_results = evaluate_categories(
                    ref_ds,
                    test_ds,
                    ContiguityCategories
                )
                for key in contiguity_results:
                    value = contiguity_results[key]
                    getattr(contiguity_records, key).append(value)
            elif meas in SHADOW_MEASUREMENT_NAMES:
                # base records
                shadow_records.granule.append(doc.granule)
                shadow_records.region_code.append(doc.region_code)
                shadow_records.reference_fname.append(str(ref_fname))
                shadow_records.test_fname.append(str(test_fname))
                shadow_records.size.append(numpy.prod(ref_ds.shape))
                shadow_records.measurement.append(meas)

                # categorical evaluation
                shadow_results = evaluate_categories(
                    ref_ds,
                    test_ds,
                    TerrainShadowCategories
                )
                for key in shadow_results:
                    value = shadow_results[key]
                    getattr(shadow_records, key).append(value)
            else:
                # null data evaluation
                null_info = evaluate_nulls(ref_ds, test_ds)
                general_records.percent_data_2_null.append(null_info[0])
                general_records.percent_null_2_data.append(null_info[1])

                diff = evaluate2(ref_ds, test_ds)
                h = distribution(diff)

                # store results
                general_records.granule.append(doc.granule)
                general_records.reference_fname.append(str(ref_fname))
                general_records.test_fname.append(str(test_fname))
                general_records.region_code.append(doc.region_code)
                general_records.size.append(diff.size)
                general_records.measurement.append(meas)

                if 'nbar' in meas or meas in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.minv.append(h['omin'] / 100)
                    general_records.maxv.append(h['omax'] / 100)
                else:
                    general_records.minv.append(h['omin'])
                    general_records.maxv.append(h['omax'])

                general_records.percent_different.append(
                    (diff != 0).sum() / diff.size * 100
                )

                # percentiles of the cumulative distribution
                h = distribution(numpy.abs(diff))
                hist = h['histogram']
                cdf = numpy.cumsum(hist / hist.sum())
                p1_idx = numpy.searchsorted(cdf, 0.9)
                p2_idx = numpy.searchsorted(cdf, 0.99)
                pct_90 = h['loc'][p1_idx]
                pct_99 = h['loc'][p2_idx]

                # percentiles from cumulative distribution
                if 'nbar' in meas or meas in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.percentile_90.append(pct_90 / 100)
                    general_records.percentile_99.append(pct_99 / 100)
                else:
                    general_records.percentile_90.append(pct_90)
                    general_records.percentile_99.append(pct_99)

    results = (
        general_records.records,
        fmask_records.records,
        contiguity_records.records,
        shadow_records.records
    )
    return results
