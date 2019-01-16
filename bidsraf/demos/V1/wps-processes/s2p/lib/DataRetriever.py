# coding: utf-8
from pywps.inout.basic import BasicBoundingBox

from ..lib.bbox_helpers import convert_bbox_to_footprint


class DataRetriever(object):
    @classmethod
    def get_data(cls, bbox, date, product_type):
        # TODO
        footprint = convert_bbox_to_footprint(bbox)


        # TODO use mock data while waiting usage of eodag
        bbox = BasicBoundingBox()
        bbox.ll = [1.2, 3.4]
        bbox.ur = [5.6, 7.8]

        return [{'product_file': 'in_file.tif',
                 'bbox': bbox}, ] * 2
