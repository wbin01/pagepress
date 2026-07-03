#!/usr/bin/env python3
import os
import hashlib
import locale
import shutil
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
        self._locales = self._locales_code()

        self._html_top, self._html_end = self._html_base()
        self._langs = self._langs_code()
        self._posts = self._all_posts()

        self._nav_langs()
        self._index()
        self._nav_pages()
        self._pages()

        self._clear()
        # self._parser = DocxParser(self._docs_path)
        # self._render = HTMLRender(self._parser)

    def _all_posts(self) -> dict:
        posts = {}

        for lang in self._langs:
            files =[f for f in (self._docs_path/lang).iterdir() if f.is_file()]
            files_ord = sorted(
                files, key=lambda x: x.stat().st_mtime, reverse=True)

            posts[lang] = {'categ': 'index', 'posts': []}
            for f in files_ord:
                posts[lang]['posts'].append(f.name)

        # for k, v in posts.items():
        #     print(k, '->', v['categ'])
        #     for x in v['posts']:
        #         print('   ', x)

        return posts

    def _clear(self) -> None:
        for node in os.listdir(self._site_path):
            if os.path.isdir(self._site_path/node) and node not in self._langs:
                # shutil.rmtree(self._site_path/node)
                with open(self._data_path/'clear.html', 'r') as file_:
                    html_clear = file_.read()
                html_clear = html_clear.replace(
                    'const defaultLang = "en-US";',
                    f'const defaultLang = "{self._langs[0]}";')
                with open(self._site_path/node/'index.html', 'w') as file_:
                    file_.write(html_clear)

    def _nav_langs(self) -> None:
        tag_li = """
            <li>
             <a class="dropdown-item" onclick="changeLang('#lang')" href="{}">
              <img {} src="{}" onerror="{}; this.src='{}';" width="20" />
              #lang
             </a>
            </li>
            """.replace(' '*12, ' '*9).format(
                '../#lang/index.html', 'class="m-1"',
                'https://hatscripts.github.io/circle-flags/flags/#icon.svg',
                'this.onerror=null',
                'https://hatscripts.github.io/circle-flags/flags/xx.svg')

        langs = ''
        for lang in self._langs:
            icon = lang.lower().split('-')[1] if '-' in lang else lang.lower()
            langs += tag_li.replace('#lang', lang).replace('#icon', icon)

        if len(self._langs) == 1:
            self._html_top = self._html_top.replace(
                '<a class="nav-link dropdown-toggle" id="currentLang" '
                'href="#" role="button" data-bs-toggle="dropdown" '
                'aria-expanded="false"> en-US </a>', '<span></span>')

        self._html_top = self._html_top.replace('<!-- LANGS -->', langs)

    def _nav_pages(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                index = file_.read()

            li_itens = ''
            for node in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/node):
                    li_itens += """
                        <li class="nav-item">
                         <a class="nav-link {} href="{}/index.html">{}</a>
                        </li>
                        """.replace(' '*24, ' '*5).format(
                            'active" aria-current="page"',
                            node, node)

            new_index = index.replace('<!-- NAV ITEM -->', li_itens)
            with open(self._site_path/lang/'index.html', 'w+') as f:
                f.write(new_index)
    
    def _index(self) -> None:
        index_start = self._html_top.replace(
            '<html lang="en-US"',
            f'<html lang="{self._default_lang}"').replace(
            '// REDIRECT',
            "window.location.replace(`${savedLang}/index.html`);").replace(
            '// CLEAR', '',).replace('#BRAND', 'index.html')

        with open(self._site_path/'index.html', 'w+') as index:
            index.write(index_start)
            index.write(self._html_end)

        for lang in self._langs:
            file_path = self._site_path/lang/'index.html'
            file_path.parent.mkdir(parents=True, exist_ok=True)

            html_start = self._html_top.replace(
                '<html lang="en-US"', f'<html lang="{lang}"').replace(
                '#BRAND', f'../{lang}/index.html')

            with open(file_path, 'w+') as index:
                index.write(html_start)
                index.write(self._html_end)

    def _pages(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                html = file_.read()

            # Brand link
            html = html.replace(
                f'href="../{lang}/index.html"',
                f'href="../../{lang}/index.html"')

            # Langs link
            for l in self._langs:
                html = html.replace(
                    f"""changeLang('{l}')" href="../{l}/index.html">""",
                    f"""changeLang('{l}')" href="../../{l}/index.html">""")

            # Pages link
            for i in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/i):
                    html = html.replace(
                        f'href="{i}/index.html"',
                        f'href="../{i}/index.html"')

            for inode in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/inode):
                    path = self._site_path/lang/inode/'index.html'
                    path.parent.mkdir(parents=True, exist_ok=True)

                    with open(path, 'w') as file_:
                        file_.write(html)

    def _html_base(self) -> list:
        with open(self._data_path/'index.html', 'r') as file_:
            html = file_.read()
        return html.split('<!-- / -->')

    def _hash(self, path: str):
        h = hashlib.new('md5')  # sha256
        with open(path, 'rb') as file_:
            while True:
                data = file_.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    def _langs_code(self) -> list:
        langs = []
        for lang_dir in os.listdir(self._docs_path):
            if os.path.isdir(self._docs_path/lang_dir):
                if os.listdir(self._docs_path/lang_dir):
                    langs.append(lang_dir)

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


if __name__ == '__main__':
    pass
