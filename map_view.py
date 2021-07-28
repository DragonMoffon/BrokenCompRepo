import random
from array import array
from PIL import Image

import arcade
import arcade.gl as gl

import Delaunator
from constants import *
from voronoi import *
import perlin


def make_perlin_image():
    tree = perlin.PerlinTree(depth=4)
    image = Image.new("RGBA", [SCREEN_WIDTH//4, SCREEN_HEIGHT//4])
    for x in range(image.width):
        for y in range(image.height):
            print(x, y)
            nx = 8*x/480
            ny = 8*y/270
            value = perlin.original_perlin_2d(tree, 0, nx, ny)*0.5 + 0.5
            for i in range(1, tree.depth):
                i2 = i*2
                value += perlin.original_perlin_2d(tree, i, nx*i2, ny*i2) / i2

            print(value)
            image.putpixel([x, y], (int(255*value), int(255*value), int(255*value), 255))

    return image.tobytes()


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


def load_buffer_voronoi(data, points, perlin_grid):
    for voronoi_polygon in data:
        base_point = points[voronoi_polygon[0]]
        print(base_point)
        elevation = ((perlin.simplex_perlin_2d(perlin_grid[0], 0, *base_point)) + 1)/2
        moisture = ((perlin.simplex_perlin_2d(perlin_grid[1], 0, *base_point)) + 1)/2
        for i in range(1, 8):
            i2 = i*2
            elevation += perlin.simplex_perlin_2d(perlin_grid[0], 0, base_point[0]*i2, base_point[1]*i2)/i2
            moisture += perlin.simplex_perlin_2d(perlin_grid[1], 0, base_point[0]*i2, base_point[1]*i2)/i2

        color = (base_point[0]+1.5)/3, (base_point[1]+1.5)/3, 0.5
        prev_point = voronoi_polygon[1][0]
        for vertex in voronoi_polygon[1][::-1]:
            triangle = base_point, prev_point, vertex
            for point in triangle:
                for coord in point:
                    yield coord
                yield clamp(elevation, 0, 1)
                yield clamp(moisture, 0, 1)
            prev_point = vertex


def draw_edge(edge, start, end):
    arcade.draw_line(*expand2d(*start), *expand2d(*end), arcade.color.BLACK)


class RenderView(arcade.View):

    def __init__(self):
        super().__init__()
        self.voronoi_program = self.window.ctx.load_program(
            vertex_shader=arcade.resources.shaders.vertex.default_projection,
            fragment_shader="shaders/uv_frag.glsl")

        self.rect_render_program = self.window.ctx.load_program(
            vertex_shader=arcade.resources.shaders.vertex.default_projection,
            fragment_shader="shaders/uv_frag.glsl")
        self.filter_render_program = self.window.ctx.load_program(
            vertex_shader=arcade.resources.shaders.vertex.default_projection,
            fragment_shader="shaders/crt_frag.glsl")

        self.perlin_texture = self.window.ctx.texture((SCREEN_WIDTH//4, SCREEN_HEIGHT//4), data=make_perlin_image(),
                                                      filter=(gl.NEAREST, gl.NEAREST))
        self.perlin_test = gl.geometry.screen_rectangle(-1, -1, 2, 2)

        self.voronoi_texture = self.window.ctx.texture((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.voronoi_screen = self.window.ctx.framebuffer(color_attachments=[self.voronoi_texture])

        self.voronoi_renderer = gl.geometry.screen_rectangle(-1, -1, 2, 2)

        self.x_adjustment = 0

        self.filter = False

        self.reload()

    def reload(self):
        arcade.start_render()
        self.voronoi_screen.use()
        self.voronoi_screen.clear()
        self.window.biome_texture.use(0)
        self.perlin_texture.use(0)
        self.perlin_test.render(self.voronoi_program)
        self.window.use()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.R:
            self.reload()
        elif symbol == arcade.key.ENTER:
            self.filter = bool(1 - self.filter)

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, _buttons: int, _modifiers: int):
        if _buttons == 2:
            self.x_adjustment = (self.x_adjustment - dx) % SCREEN_WIDTH

    def on_draw(self):
        arcade.start_render()
        self.voronoi_texture.use(0)
        if self.filter:
            self.filter_render_program['x_adjustment'] = self.x_adjustment
            self.voronoi_renderer.render(self.filter_render_program)
        else:
            self.rect_render_program['x_adjustment'] = self.x_adjustment
            self.voronoi_renderer.render(self.rect_render_program)

        arcade.draw_text(str(self.x_adjustment), SCREEN_HEIGHT / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE)