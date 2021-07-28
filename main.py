import random
import math
from array import array

import arcade
import arcade.gl as gl
from Delaunator import Delaunator
from PIL import Image

from constants import *
from voronoi import *
from map_view import RenderView

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
SCALING = 1
FILTER = gl.NEAREST

biomes = Image.open('biome_texture.png')


class MapWindow(arcade.Window):

    def __init__(self):
        super().__init__(title="voronoi Map", fullscreen=True)
        arcade.set_background_color(arcade.color.WHITE_SMOKE)
        self.biome_texture = gl.Texture(self.ctx, (198, 198),
                                        data=biomes.tobytes(), filter=(gl.NEAREST, gl.NEAREST))

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE or symbol == arcade.key.X:
            self.close()


GAME_WINDOW = MapWindow()
RENDER_VIEW = RenderView()


def main():
    GAME_WINDOW.show_view(RENDER_VIEW)
    arcade.run()


if __name__ == '__main__':
    main()
