#!/usr/bin/env python

from pathlib import Path
import numpy
import h5py
import yaml
import pandas
import rasterio
import structlog

from wagl.scripts.wagl_residuals import distribution
from wagl.hdf5 import write_dataframe

from utils import FmaskCategories, evaluate2, evaluate_fmask, evaluate_nulls
from digest_yaml import Digestyaml


LOG = structlog.get_logger()


def process_yamls(yaml_pathnames, reference_dir, product_dir_name):
    reference_dir = Path(reference_dir)

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
                null_info = evaluate_nulls(ref_ds, test_ds)
                records['percent_data_2_null'].append(null_info[0])
                records['percent_null_2_data'].append(null_info[1])

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

    return records, fmask_records
