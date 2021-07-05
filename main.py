import random
import math
from array import array

import arcade
import arcade.gl as gl
from Delaunator import Delaunator

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
SCALING = 1
FILTER = gl.NEAREST

CONVEX_HULL = set()


def reset_hull():
    global CONVEX_HULL
    CONVEX_HULL = set()


def convex_add(item):
    global CONVEX_HULL
    CONVEX_HULL.add(item)


def expand(x, factor=1):
    return (x + 1) * factor / 2


def shrink(x, factor):
    return 2*x/factor - 1


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


def for_each_vornoi_edge(points, edges, triangle, next_func):
    e = 0
    while e < len(triangle):
        if e < edges[e]:
            start = triangle_center(points, triangle, triangle_of_edge(e))
            end = triangle_center(points, triangle, triangle_of_edge(edges[e]))
            next_func(e, start, end)
        e += 1


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


def for_each_vornoi_cell(points, edges, triangles, next_func):
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


def find_each_vornoi_cell(points, edges, triangles):
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


def draw_circumcenter(t, points):
    center = circumcenter(*points)
    arcade.draw_circle_filled(expand(center[0]) * SCREEN_WIDTH, expand(center[1]) * SCREEN_HEIGHT,
                              3, arcade.color.BLUE)


def draw_points(p, points, size=2, color=arcade.color.BLUE):
    arcade.draw_circle_filled(expand(p[0], SCREEN_WIDTH), expand(p[1], SCREEN_HEIGHT), 2*size, arcade.color.RADICAL_RED)
    for point in points:
        arcade.draw_circle_filled(expand(point[0], SCREEN_WIDTH), expand(point[1], SCREEN_HEIGHT),
                                  size, color)


def draw_edge(e, start, end):
    arcade.draw_line(expand(start[0]) * SCREEN_WIDTH, expand(start[1]) * SCREEN_HEIGHT,
                     expand(end[0]) * SCREEN_WIDTH, expand(end[1]) * SCREEN_HEIGHT,
                     arcade.color.BLACK)


def load_buffer_triangles(triangle, points):
    for t in range(0, len(triangle)//3):
        triangle_points = list(map(lambda p: points[p], points_of_triangle(triangle, t)))
        base_point = list(map(lambda c: sum(c)/3, zip(*triangle_points)))
        color = (base_point[0]+1.5)/3, (base_point[1]+1.5)/3, 0.5
        for point in triangle_points:
            for coord in point:
                yield coord
            for rgb_value in color:
                yield round(rgb_value, 2)


def load_buffer_vornoi(data, points):
    for vornoi_polygon in data:
        base_point = points[vornoi_polygon[0]]
        color = (base_point[0]+1.5)/3, (base_point[1]+1.5)/3, 0.5
        prev_point = vornoi_polygon[1][0]
        for vertex in vornoi_polygon[1][::-1]:
            triangle = base_point, prev_point, vertex
            for point in triangle:
                for coord in point:
                    yield coord
                for rgb_value in color:
                    yield round(rgb_value, 2)
            prev_point = vertex


class DelaunatorMap:

    def __init__(self, points):
        self.points = points
        self.triangles = Delaunator(points).triangles
        self.half_edges = Delaunator(points).halfedges
        self.hull = Delaunator(points).hull
        self.hull_rays = self.generate_rays()
        self.vornoi = self.generate_vornoi_polygons()

    def generate_rays(self):
        rays = {}
        h = self.hull[-1]
        p0, p1 = h*4, h*4
        x0, x1 = self.points[h][0], self.points[h][0]
        y0, y1 = self.points[h][1], self.points[h][1]
        i = 0
        while i < len(self.hull):
            h = self.hull[i]
            p0 = p1
            x0 = x1
            y0 = y1
            p1 = h * 4
            x1, y1 = self.points[h]
            vector = [y1-y0, x1-x0]
            rays[h] = vector
        return rays

    def generate_vornoi_polygons(self):
        data = []
        index = {}
        e = 0
        while e < len(self.triangles):
            endpoint = self.triangles[next_half_edge(e)]
            if endpoint not in index or self.half_edges[e] == -1:
                index[endpoint] = e
            e += 1
        p = 0
        while p < len(self.points):
            incoming = index[p]
            edge = edges_around_point(self.half_edges, incoming)
            triangle = map(triangle_of_edge, edge)
            vertices = list(map(lambda t: triangle_center(self.points, self.triangles, t), triangle))
            data.append([p, vertices])
            p += 1

        return data


class MapWindow(arcade.Window):

    def __init__(self):
        super().__init__(title="Vornoi Map", fullscreen=True)
        arcade.set_background_color(arcade.color.WHITE_SMOKE)

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE or symbol == arcade.key.X:
            self.close()


class RenderView(arcade.View):

    def __init__(self):
        super().__init__()
        self.points = []
        self.point_coords = {}
        self.triangles = []
        self.half_edges = []
        self.hull = []
        self.rays = []

        self.vornoi = []

        self.map = None

        self.program = self.window.ctx.load_program(vertex_shader='basic_vertex.glsl',
                                                    fragment_shader='basic_frag.glsl')
        self.buffer = None
        self.vao = None

        self.test_key = arcade.key.KEY_1
        self.test_point = 0
        self.tests = {arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3}

        self.edge_point = 0

        self.reload()
            
    def reload(self):
        reset_hull()
        resolution = 60
        normal_resolution_width = (2 * resolution) / SCREEN_WIDTH
        normal_resolution_height = (2 * resolution) / SCREEN_HEIGHT
        self.points = []
        self.point_coords = {}
        for x in range(0, SCREEN_WIDTH//resolution):
            for y in range(0, SCREEN_HEIGHT//resolution):
                low_x = 2*(x*resolution)/SCREEN_WIDTH - 1
                low_y = 2*(y*resolution) / SCREEN_HEIGHT - 1
                point = (random.uniform(low_x, low_x+normal_resolution_width),
                         random.uniform(low_y, low_y+normal_resolution_height))
                self.points.append(point)
                self.point_coords[x, y] = point

        self.triangles = Delaunator(self.points).triangles
        self.half_edges = Delaunator(self.points).halfedges
        self.hull = Delaunator(self.points).hull

        self.map = DelaunatorMap(self.points)

        self.vornoi = find_each_vornoi_cell(self.points, self.half_edges, self.triangles)

        self.buffer = self.window.ctx.buffer(data=array('f', load_buffer_vornoi(self.vornoi, self.points)))
        # self.buffer = self.window.ctx.buffer(data=array('f', load_buffer_triangles(self.triangles, self.points)))
        description = gl.BufferDescription(self.buffer, '2f 3f', ['inPos', 'inColor'])
        self.vao = self.window.ctx.geometry([description])

        self.test_key = arcade.key.KEY_1
        self.test_point = random.randint(0, len(self.triangles))

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.R:
            self.reload()
        elif symbol in self.tests:
            self.test_key = symbol

    def on_draw(self):
        arcade.start_render()
        self.vao.render(self.program, mode=self.window.ctx.TRIANGLES)

        for_each_triangle_edge(self.points, self.half_edges, self.triangles, draw_edge)
        for_each_triangle(self.points, self.triangles, draw_circumcenter)
        for_each_vornoi_edge(self.points, self.half_edges, self.triangles, draw_edge)
        # for_each_vornoi_cell(self.points, self.half_edges, self.triangles, draw_points)

        """for vornoi in self.vornoi:
            start = self.points[vornoi[0]]
            for vertex in vornoi[1]:
                arcade.draw_line(expand(start[0], SCREEN_WIDTH), expand(start[1], SCREEN_HEIGHT),
                                 expand(vertex[0], SCREEN_WIDTH), expand(vertex[1], SCREEN_HEIGHT),
                                 arcade.color.RADICAL_RED)"""

        for point in self.points:
            arcade.draw_circle_filled(expand(point[0]) * SCREEN_WIDTH, expand(point[1]) * SCREEN_HEIGHT,
                                      4, arcade.color.PURPLE)

        for hull in self.hull:
            point = self.points[hull]
            arcade.draw_circle_filled(expand(point[0]) * SCREEN_WIDTH, expand(point[1]) * SCREEN_HEIGHT,
                                      4, arcade.color.ORANGE)


GAME_WINDOW = MapWindow()
RENDER_VIEW = RenderView()


def main():
    GAME_WINDOW.show_view(RENDER_VIEW)
    arcade.run()


if __name__ == '__main__':
    main()
