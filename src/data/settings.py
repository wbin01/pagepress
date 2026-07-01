#!/usr/bin/env python3
import os
import hashlib
import locale

from pathlib import Path

from .docx_parser import DocxParser
from .html_render import HTMLRender


PATH = Path(__file__).resolve().parent.parent


class Settings(object):
    def __init__(self) -> None:
        self._docs_path = PATH/'docs'
        self._site_path = PATH/'site'

        self._default_lang = locale.getdefaultlocale()[0].replace('_', '-')
        self._lang = self._default_lang  # locale.normalize(locale)
        self._locales = [x[1].split('.') for x in locale.locale_alias.items()]
        self._set_locales_file()

        # self._parser = DocxParser(self._docs_path)
        # self._render = HTMLRender(self._parser)

    def _hash(self, path: str):
        h = hashlib.new('md5')  # sha256
        with open(path, 'rb') as arquivo:
            while True:
                data = arquivo.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    def _set_locales_file(self) -> None:
        locales = []
        for local in self._locales:
            if local[0] not in locales: locales.append(local[0])
        
        if locales: locales.sort()
        with open(self._docs_path/'langs.txt', 'w') as local_file:
            local_file.write(
                "\nYou don't need to write the correct language code — any "
                "name will do — but using the correct one helps with the "
                "site's indexing.\n\n")
            for local in locales:
                local_file.write(local.replace('_', '-') + '\n')


if __name__ == '__main__':
    pass
