from io import BytesIO


class Layout:
    def __init__(self, skin, *args, **kwargs):
        self.skin = skin

    def _execute_draw(self) -> str:
        """
        Render this layout and return the result as a bytes string.
        """
        with self.draw() as image:
            with BytesIO() as data:
                image.save(data, format='PNG')
                data.seek(0)
                return data.getvalue()

    def close(self):
        """
        Close any resources opened while rendering the layout.
        """
        if getattr(self, 'image', None):
            self.image.close()
