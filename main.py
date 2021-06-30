import arcade
import arcade.gl as gl

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
SCALING = 1
FILTER = gl.NEAREST


class MapWindow(arcade.Window):

    def __init__(self):
        super().__init__(title="Vornoi Map", fullscreen=True)

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE or symbol == arcade.key.X:
            self.close()


class RenderView(arcade.View):

    def __init__(self):
        super().__init__()


RENDER_VIEW = RenderView()


def main():
    window = MapWindow()
    window.show_view(RENDER_VIEW)
    arcade.run()


if __name__ == '__main__':
    main()
