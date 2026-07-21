#!/usr/bin/env python3
import hashlib
import locale
import shutil
from pathlib import Path

from .conf_file import ConfFile


PATH = Path(__file__).resolve().parent.parent.parent

class Conf(object):
    def __init__(self):
        self._docs_path = PATH/'docs'
        self._site_path = PATH/'site'
        self._data_path = PATH/'data'
        self._html_path = self._data_path/'html_models'

        self._default_lang = locale.getdefaultlocale()[0].replace('_', '-')
        self._lang = self._default_lang  # locale.normalize(locale)
        self._locales = self._locales_code()
        self._langs = self._langs_code()

        if not (PATH/'page.conf').is_file():
            shutil.copy(self._data_path/'page.conf', PATH/'page.conf')
        self._conf_user = ConfFile(PATH/'page.conf')
        self._conf_page = ConfFile(self._data_path/'page.conf')

    @property
    def data_path(self) -> Path:
        """..."""
        return self._data_path

    @property
    def default_lang(self) -> str:
        """..."""
        return self._default_lang

    @property
    def docs_path(self) -> Path:
        """..."""
        return self._docs_path

    @property
    def html_path(self) -> Path:
        """..."""
        return self._html_path

    @property
    def langs(self) -> str:
        """..."""
        return self._langs

    @property
    def locales(self) -> str:
        """..."""
        return self._locales

    @property
    def site_path(self) -> Path:
        """..."""
        return self._site_path

    def hash(self, path: str):
        """..."""
        h = hashlib.new('md5')  # sha256
        with open(path, 'rb') as file_:
            while True:
                data = file_.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    def user(self, name: str, key: str) -> str:
        """..."""
        if f'[{name}]' in self._conf_user.content:
            if key in self._conf_user.content[f'[{name}]']:
                return self._conf_user.content[f'[{name}]'][key]

        value = self._conf_page.content[f'[{name}]'][key]

        if f'[{name}]' not in self._conf_user.content:
            self._conf_user.content[f'[{name}]'] = {key: value}
        else:
            self._conf_user.content[f'[{name}]'][key] = value
        self._conf_user.update_file()

        if value == 'True': value = True
        if value == 'False': value = False
        return value

    def _langs_code(self) -> list:
        """..."""
        langs = []
        for path in self._docs_path.iterdir():
            if path.is_dir():
                if any(path.iterdir()):
                    langs.append(path.name)

        if not langs:
            langs.append(self._default_lang)
            file_path = self._docs_path/self._default_lang/'settings.conf'
            file_path.parent.mkdir(parents=True, exist_ok=True)

        return langs

    def _locales_code(self) -> list:
        locales_code = [
            x[1].split('.')[0] for x in locale.locale_alias.items()]

        locales = []
        for local in locales_code:
            if local not in locales: locales.append(local)
        
        if locales: locales.sort()
        with open(self._docs_path/'langs.txt', 'w') as local_file:
            local_file.write(
                "\nYou don't need to write the correct language code — any "
                "name will do — but using the correct one helps with the "
                "site's indexing.\n\n")
            for local in locales:
                local_file.write(local.replace('_', '-') + '\n')

        return locales_code

