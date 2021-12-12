import cadquery as cq
from scipy.spatial import ConvexHull as sphull
import numpy as np


debug_trace = False

def debugprint(info):
    if debug_trace:
        print(info)


def box(width, height, depth):
    return cq.Workplane("XY").box(width, height, depth)


def cylinder(radius, height, segments=100):
    shape = cq.Workplane("XY").union(cq.Solid.makeCylinder(radius=radius, height=height))
    shape = translate(shape, (0, 0, -height/2))
    return shape


def get_distance(p1, p2):
    o_zero = []
    for (elem1, elem2) in zip(p1, p2):
        o_zero.append(elem1 - elem2)

    return abs(np.sqrt(o_zero[0] ** 2 + o_zero[1] ** 2 + o_zero[2] ** 2)), o_zero


def get_connector(shape, origin, adjacent):

    o_zero = []
    for (elem1, elem2) in zip(origin, adjacent):
        o_zero.append(elem1 - elem2)

    dist = abs(np.sqrt(o_zero[0] ** 2 + o_zero[1] ** 2 + o_zero[2] ** 2))

    direction = cq.Vector(o_zero)
    pnt = cq.Vector((0, 0, 0))

    print("    Connector: \n      origin=" + str(origin) +
          "\n      adjacent=" + str(adjacent) +
          "\n      dir=" + str(direction) +
          "\n      pnt=" + str(pnt))

    connector = translate(cq.Solid.makeBox(dist, 1, 1, pnt=pnt, dir=direction), (0, 0, 0.6))
    return shape.union(connector)


def get_branch(shape, o, v):
    # dist, o_zero = get_distance(o, v)
    o_zero = []
    for (elem1, elem2) in zip(v, o):
        o_zero.append(elem1 - elem2)
    origin = cq.Vector((0, 0, o[2] / 2))
    offset = cq.Vector(o_zero)

    # dist = abs(np.sqrt((v[0] - o[0]) ** 2 + (v[1] - o[1]) ** 2 + (v[2] - o[2]) ** 2))
    dist = abs(np.sqrt(o_zero[0] ** 2 + o_zero[1] ** 2 + o_zero[2] ** 2))
    cyl = cq.Solid.makeCylinder(pnt=origin, dir=offset, radius=0.7, height=dist)
    # cyl = cq.Solid.makeCone(pnt=origin, dir=offset, radius1=1, radius2=0.5, height=dist)
    return shape.union(cyl, clean=False)  # If clean is true, the default, things go kablooey


def sphere(radius):
    return cq.Workplane('XY').union(cq.Solid.makeSphere(radius))


def cone(r1, r2, height):
    return cq.Workplane('XY').union(
        cq.Solid.makeCone(radius1=r1, radius2=r2, height=height))


def rotate(shape, angle):
    origin = (0, 0, 0)
    shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(1, 0, 0), angleDegrees=angle[0])
    shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(0, 1, 0), angleDegrees=angle[1])
    shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(0, 0, 1), angleDegrees=angle[2])
    return shape


def translate(shape, vector):
    return shape.translate(tuple(vector))


def mirror(shape, plane=None):
    debugprint('mirror()')
    return shape.mirror(mirrorPlane=plane)


def union(shapes, clean=True):
    debugprint('union()')
    shape = None
    for item in shapes:
        if shape is None:
            shape = item
        else:
            shape = shape.union(item, clean=clean)
    return shape


def add(shapes):
    debugprint('union()')
    shape = None
    for item in shapes:
        if shape is None:
            shape = item
        else:
            shape = shape.add(item)
    return shape


def difference(shape, shapes, clean=True):
    debugprint('difference()')
    for item in shapes:
        shape = shape.cut(item, clean=clean)
    return shape


def intersect(shape1, shape2):
    return shape1.intersect(shape2)


def face_from_points(points):
    # debugprint('face_from_points()')
    edges = []
    num_pnts = len(points)
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % num_pnts]
        edges.append(
            cq.Edge.makeLine(
                cq.Vector(p1[0], p1[1], p1[2]),
                cq.Vector(p2[0], p2[1], p2[2]),
            )
        )

    face = cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))

    return face

def scale(shape, factor):
    return shape.scale(factor)

def hull_from_points(points):
    # debugprint('hull_from_points()')
    hull_calc = sphull(points)
    n_faces = len(hull_calc.simplices)

    faces = []
    for i in range(n_faces):
        face_items = hull_calc.simplices[i]
        fpnts = []
        for item in face_items:
            fpnts.append(points[item])
        faces.append(face_from_points(fpnts))

    shape = cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    shape = cq.Workplane('XY').union(shape)
    return shape


def hull_from_shapes(shapes, points=None):
    # debugprint('hull_from_shapes()')
    vertices = []
    for shape in shapes:
        verts = shape.vertices()
        for vert in verts.objects:
            vertices.append(np.array(vert.toTuple()))
    if points is not None:
        for point in points:
            vertices.append(np.array(point))

    shape = hull_from_points(vertices)
    return shape


def tess_hull(shapes, sl_tol=.5, sl_angTol=1):
    # debugprint('hull_from_shapes()')
    vertices = []
    solids = []
    for wp in shapes:
        for item in wp.solids().objects:
            solids.append(item)

    for shape in solids:
        verts = shape.tessellate(sl_tol, sl_angTol)[0]
        for vert in verts:
            vertices.append(np.array(vert.toTuple()))

    shape = hull_from_points(vertices)
    return shape


def triangle_hulls(shapes):
    debugprint('triangle_hulls()')
    hulls = [cq.Workplane('XY')]
    for i in range(len(shapes) - 2):
        hulls.append(hull_from_shapes(shapes[i: (i + 3)]))

    return union(hulls)





def bottom_hull(p, height=0.001):
    debugprint("bottom_hull()")
    shape = None
    for item in p:
        vertices = []
        # verts = item.faces('<Z').vertices()
        verts = item.faces().vertices()
        for vert in verts.objects:
            v0 = vert.toTuple()
            v1 = [v0[0], v0[1], -10]
            vertices.append(np.array(v0))
            vertices.append(np.array(v1))

        t_shape = hull_from_points(vertices)

        # t_shape = translate(t_shape, [0, 0, height / 2 - 10])

        if shape is None:
            shape = t_shape

        for shp in (*p, shape, t_shape):
            try:
                shp.vertices()
            except:
                0
        shape = union([shape, hull_from_shapes((shape, t_shape))])

    return shape


def polyline(point_list):
    return cq.Workplane('XY').polyline(point_list)


# def project_to_plate():
#     square = cq.Workplane('XY').rect(1000, 1000)
#     for wire in square.wires().objects:
#         plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))


def extrude_poly(outer_poly, inner_polys=None, height=1):  # vector=(0,0,1)):
    outer_wires = cq.Wire.assembleEdges(outer_poly.edges().objects)
    inner_wires = []
    if inner_polys is not None:
        for item in inner_polys:
            inner_wires.append(cq.Wire.assembleEdges(item.edges().objects))

    return cq.Workplane('XY').add(
        cq.Solid.extrudeLinear(outerWire=outer_wires, innerWires=inner_wires, vecNormal=cq.Vector(0, 0, height)))


def import_file(fname, convexity=None):
    print("IMPORTING FROM {}".format(fname))
    return cq.Workplane('XY').add(cq.importers.importShape(
        cq.exporters.ExportTypes.STEP,
        fname + ".step"))

def export_stl(shape, fname):
    print("EXPORTING STL TO {}".format(fname))
    cq.exporters.export(shape, fname=fname + "_cadquery.stl", exportType="STL")

def export_file(shape, fname):
    print("EXPORTING TO {}".format(fname))
    cq.exporters.export(w=shape, fname=fname + ".step",
                        exportType='STEP')

    export_stl(shape, fname)


def export_dxf(shape, fname):
    print("EXPORTING TO {}".format(fname))
    cq.exporters.export(w=shape, fname=fname + ".dxf",
                        exportType='DXF')
