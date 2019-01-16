# coding: utf-8


class BoundingBox(object):
    """Simple BoundingBox"""
    def __init__(self,
                 minx: float = None,
                 miny: float = None,
                 maxx: float = None,
                 maxy: float = None,
                 crs: str = None):
            self.minx = minx
            self.miny = miny
            self.maxx = maxx
            self.maxy = maxy
            self.crs = crs

    def __str__(self):
        return "BoundingBox minx:{0.minx} miny:{0.miny} maxx:{0.maxx} maxy:{0.maxy} crs:{0.crs}".format(self)

    @classmethod
    def from_str(cls, bboxstr):
        """Parse bbox str to create a BoundingBox object
        :param string bboxstr: A string representing a bbox ex: "71.63,41.75,-70.78,42.90,urn:ogc:def:crs:EPSG::4326"
        """

        # COORDS
        coords = bboxstr.split(',')[:4]
        coords = list(map(float, coords))
        #CRS
        crs = bboxstr.split(',')[4:]

        return cls(coords[0], coords[1], coords[2], coords[3], crs[0] if crs else None)
