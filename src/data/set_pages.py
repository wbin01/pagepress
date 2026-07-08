#!/usr/bin/env python3
import re
import os
import hashlib
import locale
import shutil
from pathlib import Path

from .docx_parser import DocxParser
from .html_render import HTMLRender


PATH = Path(__file__).resolve().parent.parent


class SetPages(object):
    def __init__(self) -> None:
        self._docs_path = PATH/'docs'
        self._site_path = PATH/'site'
        self._data_path = PATH/'data'

        self._default_lang = locale.getdefaultlocale()[0].replace('_', '-')
        self._lang = self._default_lang  # locale.normalize(locale)
        self._locales = self._locales_code()

        self._html_top, self._html_end = self._html_base()
        self._langs = self._langs_code()

        with open(self._data_path/'noise.txt', 'r') as n:
            self._noise_img = n.read().replace('\n', '').strip()

        with open(self._data_path/'blank.txt', 'r') as n:
            self._blank_img = n.read().replace('\n', '').strip()

        self._nav_langs()
        self._nav_langs_index()
        self._nav_categs()
        self._nav_categs_index()
        self._index_content()
        self._clear()

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

        for lang in self._langs:
            self._delete_missing_inodes(lang)
            for inode in os.listdir(self._site_path/lang):
                if os.path.isdir(self._site_path/lang/inode):
                    self._delete_missing_inodes(f'{lang}/{inode}')

    def _delete_missing_inodes(self, inode_path):
        docs = [x for x in os.listdir(self._docs_path/inode_path)]

        for inode in os.listdir(self._site_path/inode_path):
            if inode == 'index.html': continue
            if inode.replace('.html', '.docx') not in docs:
                if os.path.isfile(self._site_path/inode_path/inode):
                    os.remove(self._site_path/inode_path/inode)
                else:
                    shutil.rmtree(self._site_path/inode_path/inode)

    def _hash(self, path: str):
        h = hashlib.new('md5')  # sha256
        with open(path, 'rb') as file_:
            while True:
                data = file_.read(65536)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()

    def _html_base(self) -> list:
        with open(self._data_path/'index.html', 'r') as file_:
            html = file_.read()
        return html.split('<!-- / -->')

    def _html_formatted_content(
            self, html: HTMLRender, top: str, end: str) -> HTMLRender:
        cover = """+
            <!-- Cover -->
            <div class="position-relative" style="width:100%; height:300px;">
             <img style="height:300px;width:100%;object-fit:cover;" src="#img">
             <div class="{}" style="background-image:url('{}'); {}"></div>
            </div>
            """.replace(' '*10, '').replace('+\n', '').format(
                'position-absolute top-0 start-0 border border-0',
                self._noise_img, 'background-repeat:repeat; height:300px; '
                'width:100%; border:0px; opacity: 0.7;')
         
        cover_alt = """+
            <!-- Cover -->
            <div class="position-relative" style="width:100%; height:100px;">
            </div>
            """.replace(' '*10, '').replace('+\n', '')
        
        title = """
            <!-- Title -->
            <div class="position-relative text-light text-center">
            <header class="position-absolute w-100 bottom-0 m-0">
             <h1 class="post-title m-0 p-1 pt-2" style="#style">#title</h1>
            </header>
            </div><div class="m-4 #pd"></div>

            <div class="container-lg">
            <!-- Content -->\n""".replace(' '*10, '')

        title_st = (
            'text-shadow: 2px 2px 5px #000;'
            'min-height: 80px; background: #000000;'
            'background: linear-gradient(0deg, rgba(0, 0, 0, 0.76) 0%, '
            'rgba(0, 0, 0, 0.6) 27%, rgba(0, 0, 0, 0) 100%);', 'pb-2')
        
        if not html.cover:
            cover = cover_alt
            title_st = 'min-height:80px;', ''
            title = title.replace('text-light', 'text-body')
            title_padding = ''
        title = title.replace('#style', title_st[0]).replace('#pd',title_st[1])

        content_end = ' </div>\n  <!-- Content end-->\n </article>'

        html.start = top
        html.cover = cover.replace('#img', html.cover_src)
        html.title = title.replace('#title', html.title_text)
        html.body = html.body.replace('</article>', content_end)
        html.end = end

        return html

    def _index_content(self) -> None:
        card = """
            <a class="text-decoration-none" href="#link">
             <div class="row m-4 p-0 position-relative text-body d-flex {} {}">
              <div class="col-md-4 m-0 p-0">
               <img src="#img_src" height="100" class="{}" alt="">
              </div>
              <div class="col-md-8 m-0 p-0 d-flex align-items-center" {}>
               <h3 class="m-0 ms-1 p-1">#title</h3>
              </div>
             </div>
            </a>
            """.replace(' '*10, '').format(
                'align-items-center shadow',
                'border border-secondary border-opacity-25',
                'card-img object-fit-cover',
                'style="min-height:70px;"')

        content = ''
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as f:
                top, end = f.read().split('<!-- CONTENT -->')

            for inode in os.listdir(self._docs_path/lang):
                if os.path.isfile(self._docs_path/lang/inode):
                    if not inode.endswith('.docx'):
                        continue

                    name = inode.replace('.docx', '.html')
                    html = HTMLRender(DocxParser(self._docs_path/lang/inode))
                    html = self._html_formatted_content(html, top, end)
                    html.save(self._site_path/lang/name)

                    if not html.cover_src: html.cover_src = self._blank_img
                    content += card.replace(
                        '#title', html.title_text).replace(
                        '#link', name).replace(
                        '#img_src', html.cover_src)
                else:
                    self._index_content_for_categs(lang, inode, card)

            with open(self._site_path/lang/'index.html', 'w+') as f:
                f.write(f'{top}{content}{end}')

    def _index_content_for_categs(
            self, lang: str, inode: str, card: str) -> None:
        sub_content = ''
        with open(self._site_path/lang/inode/'index.html', 'r') as f:
            top, end = f.read().split('<!-- CONTENT -->')

        for item in os.listdir(self._docs_path/lang/inode):
            if os.path.isdir(self._docs_path/lang/inode/item): continue
            if not item.endswith('.docx'):
                continue
            
            name = item.replace('.docx', '.html')
            html = HTMLRender(DocxParser(self._docs_path/lang/inode/item))
            html = self._html_formatted_content(html, top, end)
            html.save(self._site_path/lang/inode/name)

            if not html.cover_src: html.cover_src = self._blank_img
            sub_content += card.replace(
                '#title', html.title_text).replace(
                '#link', name).replace(
                '#img_src', html.cover_src)

        with open(self._site_path/lang/inode/'index.html', 'w') as f:
            f.write(f'{top}{sub_content}{end}')

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

    def _nav_categs(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                index = file_.read()

            li_itens = ''
            for node in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/node):
                    li_itens += """
                        <li class="nav-item">
                         <a {} class="nav-link" href="{}/index.html">{}</a>
                        </li>
                        """.replace(' '*24, ' '*5).format(
                            'aria-current="page"', node, node)

            new_index = index.replace('<!-- NAV ITEM -->', li_itens)
            with open(self._site_path/lang/'index.html', 'w+') as f:
                f.write(new_index)

    def _nav_categs_index(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                html = file_.read()

            html = self._update_nav_links(lang, html, 'CATEG')
            for inode in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/inode):
                    path = self._site_path/lang/inode/'index.html'
                    path.parent.mkdir(parents=True, exist_ok=True)

                    n_html = html
                    r = re.findall(r'-link\" href=\"[^\"]+\">' + inode, n_html)
                    if r:
                        n = r[0].replace('-link', '-link active')
                        n_html = n_html.replace(r[0], n)

                    with open(path, 'w') as file_:
                        file_.write(n_html)

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
    
    def _nav_langs_index(self) -> None:
        index_start = self._html_top.replace(
            '<html lang="en-US"',
            f'<html lang="{self._default_lang}"').replace(
            '// REDIRECT',
            "window.location.replace(`${savedLang}/index.html`);").replace(
            '#BRAND', 'index.html')

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
                index.write(html_start + '\n<!-- CONTENT -->')
                index.write(self._html_end)

    def _update_nav_links(self, lang: str, html: str, level: str) -> str:
        if level == 'CATEG':
            brand_prev, brand_next = '../', '../../'
            langs_prev, langs_next = '../', '../../'
            pages_prev, pages_next = ''   , '../'

        elif level == 'SUB-CATEG':
            brand_prev, brand_next = '../../', '../../../'
            langs_prev, langs_next = '../../', '../../../'
            pages_prev, pages_next = '../'   , '../../'

        # Brand link
        html = html.replace(
            f'href="{brand_prev}{lang}/index.html"',
            f'href="{brand_next}{lang}/index.html"')

        # Langs link
        for l in self._langs:
            html = html.replace(
                f"""changeLang('{l}')" href="{langs_prev}{l}/index.html">""",
                f"""changeLang('{l}')" href="{langs_next}{l}/index.html">""")

        # Pages link
        for i in os.listdir(self._docs_path/lang):
            if os.path.isdir(self._docs_path/lang/i):
                html = html.replace(
                    f'href="{pages_prev}{i}/index.html"',
                    f'href="{pages_next}{i}/index.html"')
        return html


if __name__ == '__main__':
    pass
