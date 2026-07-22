import base64
from pathlib import Path

from .svg_icon_to_html import SvgIconToHTML


class Img(object):
    """..."""
    def __init__(self) -> None:
        """..."""
        self._supported_ext = ['.png', '.jpg', '.jpeg']

    @property
    def supported_ext(self) -> list:
        """..."""
        return self._supported_ext

    def base64(self, path: Path, fallback: str = '') -> str:
        """..."""
        if not path.is_file():
            return fallback

        if path.suffix.lower() == '.txt':
            with open(path, 'r') as f:
                return f.read()

        if path.suffix.lower() not in self._supported_ext:
            return fallback

        with open(path, 'rb') as f:
            src = base64.b64encode(f.read()).decode('ascii')
            return f'data:image/{path.suffix};base64,{src}'

    def icon(self, name: str) -> str:
        return SvgIconToHTML('close').html
 