#!/usr/bin/env python3
import re
from pathlib import Path
from scour import scour


PATH = Path(__file__).resolve().parent.parent.parent


class SvgIconToHTML(object):
    def __init__(self, name: str, path: str = 'default') -> None:
        self._name = name
        self._path = PATH/'data'/'icons'/path/f'{name}.svg' # .as_posix()
        self._html = None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self._name}")'

    @property
    def html(self) -> str:
        if self._html:
            return self._html

        options = scour.sanitizeOptions()
        options.remove_metadata = True
        options.strip_xml_prolog = True
        # options.enable_viewboxing = True

        with open(self._path, 'r', encoding='utf-8') as f:
            svg_text = f.read()

        optimized = scour.scourString(svg_text, options)
        optimized = re.sub(r'\s*fill\s*=\s*\"#[^\"]*\"', '', optimized.strip())
        if 'class="' not in optimized:
            optimized = optimized.replace('<svg ', '<svg class="" ')

        if 'fill="currentColor"' not in optimized:
            optimized = optimized.replace(
                'class="', 'fill="currentColor" class="')

        if self._name == 'book':
            optimized = optimized.replace(
                'class="', 'style="margin:0px 0px 2px 2px;" class="')
        else:
            optimized = optimized.replace(
                'class="', 'style="margin:0px 0px 2px 0px;" class="')

        if self._name:
            html = optimized.replace('<svg', f'<svg name="{self._name}"')
        else:
            html = optimized

        self._html = html.replace('\n', '').strip()

        return self._html

if __name__ == '__main__':
    icon = SvgIconToHTML('close')
    print(icon)
    print(icon.html)
