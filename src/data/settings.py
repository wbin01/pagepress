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
        self._data_path = PATH/'data'

        self._default_lang = locale.getdefaultlocale()[0].replace('_', '-')
        self._lang = self._default_lang  # locale.normalize(locale)
        self._locales = []
        self._set_locales()

        self._site_langs = []

        self._html_start = None
        self._html_end = None
        self._set_html_base()

        self._set_lang()
        self._set_index_html()

        # self._parser = DocxParser(self._docs_path)
        # self._render = HTMLRender(self._parser)

    def _set_lang(self) -> None:
        self._site_langs = []
        for lang_dir in os.listdir(self._docs_path):
            if os.path.isdir(self._docs_path/lang_dir):
                if os.listdir(self._docs_path/lang_dir):
                    self._site_langs.append(lang_dir)

        if not self._site_langs:
            self._site_langs.append(self._default_lang)
            file_path = self._docs_path/self._default_lang/'settings.conf'
            file_path.parent.mkdir(parents=True, exist_ok=True)

        space = '         '
        img_err = ("this.onerror=null; this.src='https://hatscripts.github.io/"
            "circle-flags/flags/xx.svg';")
        tag_li = (
            space + '<li>\n' +
            space + ' <a class="dropdown-item" onclick="changeLang(#LANG)" '
            'href="#lang/index.html">\n' +
            space + '  <img class="m-1" src="https://hatscripts.github.io/c'
            f'ircle-flags/flags/#icon.svg" onerror="{img_err}" width="20" />'
            ' #lang\n' +
            space + ' </a>\n' +
            space + '</li>\n')

        li_langs = '\n'
        for lang in self._site_langs:
            icon = lang.lower().split('-')[1] if '-' in lang else lang.lower()
            script = f"'{lang}'"
            li_langs += tag_li.replace(
                '#LANG', script).replace('#lang', lang).replace('#icon', icon)

        if len(self._site_langs) < 2:
            self._html_start = self._html_start.replace(
                '<a class="nav-link dropdown-toggle" id="currentLang" '
                'href="#" role="button" data-bs-toggle="dropdown" '
                'aria-expanded="false"> en-US </a>', '<span></span>')

        self._html_start = self._html_start.replace('<!-- LANGS -->', li_langs)
    
    def _set_index_html(self) -> None:
        redirect = (
            f'const defaultLang = "{self._site_langs[0]}";\n'
            "  const targetUrl = `${savedLang}/index.html`;\n"
            "  fetch(targetUrl, { method: 'HEAD' })\n"
            "      .then(response => {\n"
            "          if (response.ok) {\n"
            "              window.location.replace(targetUrl);\n"
            "          } else {\n"
            "              tratarIdiomaInvalido();\n"
            "          }\n"
            "      })\n"
            "      .catch(() => {\n"
            "          tratarIdiomaInvalido();\n"
            "      });\n"
            "\n"
            "  function tratarIdiomaInvalido() {\n"
            "      localStorage.setItem('page_lang', defaultLang);"
            "      document.cookie = `lang=${defaultLang}; path=/; max-age=31536000`;\n"
            "      window.location.replace(`${defaultLang}/index.html`);\n"
            "  }")

        html_start = self._html_start.replace(
            '<html lang="en-US"',
            f'<html lang="{self._site_langs[0]}"').replace(
            '// REDIRECT', redirect)

        with open(self._site_path/'index.html', 'w+') as index:
            index.write(html_start)
            index.write(self._html_end)

        html_start = self._html_start
        for lang in self._site_langs:
            html_start = html_start.replace(
                lang + '/index.html',  f'../{lang}/index.html')

        for lang in self._site_langs:
            file_path = self._site_path/lang/'index.html'
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w+') as index:
                index.write(html_start)
                index.write(self._html_end)

    def _set_html_base(self) -> str:
        with open(self._data_path/'index.html', 'r') as file_:
            html = file_.read()
        self._html_start, self._html_end = html.split('<!-- / -->')

    def _hash(self, path: str):
        h = hashlib.new('md5')  # sha256
        with open(path, 'rb') as file_:
            while True:
                data = file_.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    def _set_locales(self) -> None:
        self._locales = [
            x[1].split('.')[0] for x in locale.locale_alias.items()]

        locales = []
        for local in self._locales:
            if local not in locales: locales.append(local)
        
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
