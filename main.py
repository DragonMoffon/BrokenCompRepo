import random
import math
from array import array

import arcade
import arcade.gl as gl
from Delaunator import Delaunator

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
SCALING = 1
FILTER = gl.NEAREST


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
    vertices = map(lambda p: points[p], points_of_triangle(triangles, t))
    return circumcenter(*vertices)


def next_half_edge(e):
    if e % 3 == 2:
        return e-2
    return e+1


def prev_half_edge(e):
    if e % 3 == 2:
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
    result.append(incoming)
    outgoing = next_half_edge(incoming)
    incoming = edges[outgoing]
    while incoming != 1 and incoming != start:
        result.append(incoming)
        outgoing = next_half_edge(incoming)
        incoming = edges[outgoing]

    return result


def for_each_vornoi_cell(points, edges, triangles, next_func):
    seen = set()
    e = 0
    while e < len(triangles):
        start = triangles[next_half_edge(e)]
        if start not in seen:
            seen.add(start)
            edge = edges_around_point(edges, start)
            triangle = map(triangle_of_edge, edge)
            vertices = map(lambda t: triangle_center(points, triangles, t), triangle)
            next_func(start, vertices)
        e += 1


def find_each_vornoi_cell(points, edges, triangles):
    data = []
    seen = set()
    e = 0
    while e < len(triangles):
        start = triangles[next_half_edge(e)]
        if start not in seen:
            seen.add(start)
            edge = edges_around_point(edges, start)
            triangle = list(map(triangle_of_edge, edge))
            vertices = list(map(lambda t: triangle_center(points, triangles, t), triangle))
            data.append([start, vertices])
        e += 1

    return data


def draw_circumcenter(t, points):
    center = circumcenter(*points)
    arcade.draw_circle_filled(expand(center[0]) * SCREEN_WIDTH, expand(center[1]) * SCREEN_HEIGHT,
                              3, arcade.color.BLUE)


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
        print(base_point)
        color = (base_point[0]+1.5)/3, (base_point[1]+1.5)/3, 0.5
        print('vornoi')
        for vertex in vornoi_polygon[1]:
            print(vertex)
            for coord in vertex:
                yield coord
            for rgb_value in color:
                yield round(rgb_value, 2)


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
        self.triangles = []
        self.half_edges = []
        self.colors = []

        self.program = self.window.ctx.load_program(vertex_shader='basic_vertex.glsl',
                                                    fragment_shader='basic_frag.glsl')
        self.buffer = None
        self.vao = None

        self.reload()
            
    def reload(self):
        resolution = 60
        normal_resolution_width = (2 * resolution) / SCREEN_WIDTH
        normal_resolution_height = (2 * resolution) / SCREEN_HEIGHT
        self.points = []
        for x in range(-1, SCREEN_WIDTH//resolution + 1):
            for y in range(-1, SCREEN_HEIGHT//resolution + 1):
                low_x = 2*(x*resolution)/SCREEN_WIDTH - 1
                low_y = 2*(y*resolution) / SCREEN_HEIGHT - 1
                point = (random.uniform(low_x, low_x+normal_resolution_width),
                         random.uniform(low_y, low_y+normal_resolution_height))
                self.points.append(point)
        self.triangles = Delaunator(self.points).triangles
        self.half_edges = Delaunator(self.points).halfedges

        self.buffer = self.window.ctx.buffer(data=array('f', load_buffer_vornoi(find_each_vornoi_cell(self.points,
                                                                                                      self.half_edges,
                                                                                                      self.triangles),
                                                                                self.points)))
        # self.buffer = self.window.ctx.buffer(data=array('f', load_buffer_triangles(self.triangles, self.points)))
        description = gl.BufferDescription(self.buffer, '2f 3f', ['inPos', 'inColor'])
        self.vao = self.window.ctx.geometry([description])

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.R:
            self.reload()

    def on_draw(self):
        arcade.start_render()
        self.vao.render(self.program, mode=self.window.ctx.TRIANGLES)

        # for_each_triangle_edge(self.points, self.half_edges, self.triangles, draw_edge)
        for_each_triangle(self.points, self.triangles, draw_circumcenter)
        for_each_vornoi_edge(self.points, self.half_edges, self.triangles, draw_edge)

        for point in self.points:
            arcade.draw_circle_filled(expand(point[0]) * SCREEN_WIDTH, expand(point[1]) * SCREEN_HEIGHT,
                                      4, arcade.color.RED)


GAME_WINDOW = MapWindow()
RENDER_VIEW = RenderView()


def main():
    GAME_WINDOW.show_view(RENDER_VIEW)
    arcade.run()


if __name__ == '__main__':
    main()
