# coding: utf-8
from pyproj import Proj, transform
from pywps import BoundingBoxInput

from ..lib.BoundingBox import BoundingBox

WGS_4326 = Proj("+init=EPSG:4326")
WGS_3857 = Proj("+init=EPSG:3857")


def bbox_from_bboxinput(bboxin: BoundingBoxInput) -> BoundingBox :
    minx, miny, maxx, maxy = list(map(float, bboxin.data))
    return BoundingBox(minx, miny, maxx, maxy, bboxin.crs)


def convert_bbox_to_footprint(bbox, out_proj=WGS_4326):
    bbox, in_proj = _get_bbox_and_proj(bbox, WGS_3857)
    x1, y1, x2, y2 = change_projection(bbox, in_proj, out_proj)

    # Format footprint
    rv = {'lonmin': x1,
          'latmin': y1,
          'lonmax': x2,
          'latmax': y2}
    return rv


def convert_bbox_to_polygon(bbox, out_proj=WGS_3857):
    bbox, in_proj = _get_bbox_and_proj(bbox, WGS_3857)

    x1, y1, x2, y2 = change_projection(bbox, in_proj, out_proj)

    coords = [[x1, y1], [x1, y2], [x2, y2], [x2, y1], [x1, y1]]

    # Format extent
    rv = {"type": "Polygon",
          "coordinates": [coords]}
    return rv


def _as_proj(proj_or_crs):
    rv = proj_or_crs
    if not isinstance(proj_or_crs, Proj):
        rv = Proj("+init=" + proj_or_crs)

    return rv


def _get_bbox_and_proj(bbox, default_proj=None):
    if isinstance(bbox, BoundingBoxInput):
        # Retrieve crss
        crs = bbox.crs
        proj = Proj("+init=" + crs)
        bbox = map(float, bbox.data)
    elif not isinstance(bbox, list):
        raise ValueError('Unexpected bbox type')
    else:
        proj = _as_proj(default_proj)

    return bbox, proj


def change_projection(bbox, in_proj, out_proj):
    in_proj = _as_proj(in_proj)
    out_proj = _as_proj(out_proj)

    minx, miny, maxx, maxy = bbox
    xx, yy = transform(in_proj, out_proj, [minx, maxx], [miny, maxy])
    return xx[0], yy[0], xx[1], yy[1]