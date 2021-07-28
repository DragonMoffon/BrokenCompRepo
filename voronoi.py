import random
import math

from Delaunator import Delaunator

from constants import *


# ---- HELPER FUNCTIONS ---- #
def edges_of_triangle(t):
    return [t*3, t*3 + 1, t*3 + 2]


def points_of_triangle(triangles, t):
    return map(lambda e: triangles[e], edges_of_triangle(t))


def triangle_of_edge(e):
    return math.floor(e/3)


def triangle_adjacent_to_triangle(edges, t):
    adjacent_triangles = []
    for e in edges_of_triangle(t):
        opposite = edges[e]
        if opposite >= 0:
            adjacent_triangles.append(triangle_of_edge(opposite))

    return adjacent_triangles


def circumcenter(a, b, c):
    ad = a[0]**2 + a[1]**2
    bd = b[0]**2 + b[1]**2
    cd = c[0]**2 + c[1]**2
    D = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    return [
        1 / D * (ad * (b[1] - c[1]) + bd * (c[1] - a[1]) + cd * (a[1] - b[1])),
        1 / D * (ad * (c[0] - b[0]) + bd * (a[0] - c[0]) + cd * (b[0] - a[0])),
    ]


def triangle_center(points, triangles, t):
    vertices = list(map(lambda p: points[p], points_of_triangle(triangles, t)))
    return circumcenter(*vertices)


def next_half_edge(e):
    if e % 3 == 2:
        return e-2
    return e+1


def prev_half_edge(e):
    if e % 3 == 0:
        return e+2
    return e-1


def find_centroid(vertices):
    centroid_x = 0
    centroid_y = 0
    i = 0
    while i < len(vertices):
        centroid_x += vertices[i][0]
        centroid_y += vertices[i][1]
        i += 1

    return centroid_x/len(vertices), centroid_y/len(vertices)


def edges_around_point(edges, start):
    result = []
    incoming = start
    while True:
        result.append(incoming)
        outgoing = next_half_edge(incoming)
        incoming = edges[outgoing]
        if incoming != -1 and incoming != start:
            continue
        break

    return result


# ---- FOR FUNCTIONS ---- #
def for_each_triangle_edge(points, edges, triangles, next_func):
    e = 0
    while e < len(triangles):
        if e > edges[e]:
            start = points[triangles[e]]
            end = points[triangles[next_half_edge(e)]]
            next_func(e, start, end)
        e += 1


def for_each_triangle(points, triangles, next_func):
    t = 0
    while t < len(triangles)//3:
        next_func(t, map(lambda p: points[p], points_of_triangle(triangles, t)))
        t += 1


def for_each_voronoi_edge(points, edges, triangle, next_func):
    e = 0
    while e < len(triangle):
        if e < edges[e]:
            start = triangle_center(points, triangle, triangle_of_edge(e))
            end = triangle_center(points, triangle, triangle_of_edge(edges[e]))
            next_func(e, start, end)
        e += 1


def for_each_voronoi_cell(points, edges, triangles, next_func):
    index = {}
    e = 0
    while e < len(triangles):
        endpoint = triangles[next_half_edge(e)]
        if endpoint not in index or edges[e] == -1:
            index[endpoint] = e
        e += 1
    p = 0
    while p < len(points):
        incoming = index[p]
        edge = edges_around_point(edges, incoming)
        triangle = map(triangle_of_edge, edge)
        vertices = list(map(lambda t: triangle_center(points, triangles, t), triangle))
        next_func([p, vertices])
        p += 1


# ---- VORONOI DATA CLASSES ---- #
def find_each_voronoi_cell(points, edges, triangles):
    data = []
    index = {}
    e = 0
    while e < len(triangles):
        endpoint = triangles[next_half_edge(e)]
        if endpoint not in index or edges[e] == -1:
            index[endpoint] = e
        e += 1
    p = 0
    while p < len(points):
        incoming = index[p]
        edge = edges_around_point(edges, incoming)
        triangle = map(triangle_of_edge, edge)
        vertices = list(map(lambda t: triangle_center(points, triangles, t), triangle))
        data.append([p, vertices])
        p += 1

    return data


class VoronoiVertex:

    def __init__(self, pos, neighbors):
        self.parent_points: list
        self.position: list[float, float] = pos
        self.neighbors: list[VoronoiVertex] = neighbors
        self.elevation: float = 0
        self.moisture: float = 0


class VoronoiPoint:

    def __init__(self, pos, voronoi_map):
        self.map = voronoi_map
        self._position: list[float, float] = pos
        self._voronoi_vertices: list[VoronoiVertex] = []
        self._point_neighbors: list[VoronoiPoint] = []
        self._buffer_polygons: list[list[float, float]] = []

    def update_vertices(self):
        pass

    @property
    def pos(self):
        return self._position

    @pos.setter
    def pos(self, value):
        self._position = value
        self.map.update()
        self.update_vertices()

    @property
    def screen_pos(self):
        return expand2d(*self._position)

    @screen_pos.setter
    def screen_pos(self, value):
        self.pos = shrink2d(*value)

    @property
    def x(self):
        return self._position[0]

    @property
    def y(self):
        return  self._position[1]

    @property
    def neighbours(self):
        if not len(self._point_neighbors):
            pass
        return self._point_neighbors


class VoronoiMap:
    resolution = 4

    def __init__(self):
        self.points = []
        self.points_coords = {}
        self.edges = []
        self.triangles = []
        self.voronoi_points: list[VoronoiPoint] = []
        self.voronoi_vertices: list[VoronoiVertex] = []

    def load_map(self):
        self.points = []
        self.points_coords = {}
        self.edges = []
        self.triangles = []
        self.voronoi_points: list[VoronoiPoint] = []

        normal_resolution_width = (2 * self.resolution) / SCREEN_WIDTH
        normal_resolution_height = (2 * self.resolution) / SCREEN_HEIGHT

        # Generate the base set of points
        for x in range(0, SCREEN_WIDTH // normal_resolution_width+1):
            for y in range(0, SCREEN_HEIGHT // normal_resolution_height+1):
                low_x = 2 * (x * self.resolution) / SCREEN_WIDTH - 1
                low_y = 2 * (y * self.resolution) / SCREEN_HEIGHT - 1
                point = [random.uniform(low_x, low_x + normal_resolution_width),
                         random.uniform(low_y, low_y + normal_resolution_height)]
                voronoi_point = VoronoiPoint(point, self)
                self.points.append(point)
                self.voronoi_points.append(voronoi_point)
                self.points_coords[x, y] = len(self.points)-1

        # use centroids to spread out the voronoi sectors
        for i in range(3):
            self.triangles = Delaunator(self.points).triangles
            self.edges = Delaunator(self.points).halfedges
            voronoi = find_each_voronoi_cell(self.points, self.edges, self.triangles)
            for voronoi in voronoi:
                centroid = find_centroid(voronoi[1])
                point = self.points[voronoi[0]]
                point[0] = centroid[0]
                point[1] = centroid[1]

        self.triangles = Delaunator(self.points).triangles
        self.edges = Delaunator(self.points).halfedges

    def update(self):
        self.edges = Delaunator(self.points).halfedges
        self.triangles = Delaunator(self.points).triangles
