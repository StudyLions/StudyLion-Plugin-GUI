import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class Layout:
    def __init__(self, skin, *args, **kwargs):
        self.skin = skin

    def _execute_draw(self) -> str:
        """
        Render this layout and return the result as a bytes string.
        """
        # import time
        # starting = time.time()
        with self.draw() as image:
            # logger.debug(f"Drawing complete after {time.time() - starting} seconds")
            with BytesIO() as data:
                image.save(data, format='PNG', compress_type=3, compress_level=1)
                # logger.debug(f"Saving complete after {time.time() - starting} seconds")
                data.seek(0)
                bytes = data.getvalue()
                # logger.debug(f"Raw rendering took {time.time() - starting} seconds")
                return bytes

    def close(self):
        """
        Close any resources opened while rendering the layout.
        """
        if getattr(self, 'image', None):
            self.image.close()
