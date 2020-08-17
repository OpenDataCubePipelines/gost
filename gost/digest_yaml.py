#!/usr/bin/env python

import yaml


class Digestyaml:
    def __init__(self, pathname):
        with open(str(pathname)) as src:
            self._doc = yaml.load(src, Loader=yaml.FullLoader)

        if 'product_type' in self._doc:
            self._eo3 = False
            key = list(self._doc['lineage']['source_datasets'].keys())[0]
            self._product_name = self._doc['product_type']
            try:
                # Sentinel-2 Collection-1
                self._granule = self._doc['lineage']['source_datasets'][key]['tile_id']
                # self._region_code = self._doc['lineage']['source_datasets'][key]['image']['tile_reference'][1:]
                self._region_code = self._granule.split('_')[-2][1:]
            except KeyError:
                # Landsat Collection-2
                self._granule = self._doc['lineage']['source_datasets']['level1']['usgs']['scene_id']
                xy = self._doc['lineage']['source_datasets']['level1']['image']['satellite_ref_point_start']
                path = xy['x']
                row = xy['y']
                self._region_code = f"{path:03}{row:03}"
                
            self._measurements = self._doc['image']['bands']
        else:
            # Landsat Collection-3
            self._eo3 = True
            self._product_name = self._doc['product']['name']
            self._granule = self._doc['properties']['landsat:landsat_scene_id']
            self._region_code = self._doc['properties']['odc:region_code']
            self._measurements = self._doc['measurements']
            self._parent_uuid = self._doc['lineage']['level1'][0]  # assuming a single level-1 source

    @property
    def doc(self):
        return self._doc

    @property
    def eo3(self):
        return self._eo3

    @property
    def product_name(self):
        return self._product_name

    @property
    def granule(self):
        return self._granule

    @property
    def region_code(self):
        return self._region_code

    @property
    def measurements(self):
        return self._measurements

    @property
    def parent_uuid(self):
        return self._parent_uuid
