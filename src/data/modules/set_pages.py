#!/usr/bin/env python3
import re
import os
import hashlib
import locale
import shutil
from pathlib import Path

from .conf_file import ConfFile
from .docx_html import DocxHTML
from .svg_icon_to_html import SvgIconToHTML


PATH = Path(__file__).resolve().parent.parent.parent


class SetPages(object):
    def __init__(self) -> None:
        self._docs_path = PATH/'docs'
        self._site_path = PATH/'site'
        self._data_path = PATH/'data'
        self._html_path = self._data_path/'html_models'

        self._default_lang = locale.getdefaultlocale()[0].replace('_', '-')
        self._lang = self._default_lang  # locale.normalize(locale)
        self._locales = self._locales_code()

        self._html_top, self._html_end = self._html_base()
        self._langs = self._langs_code()

        with open(self._data_path/'img64'/'noise.txt', 'r') as n:
            self._noise_img = n.read().replace('\n', '').strip()

        with open(self._data_path/'img64'/'blank.txt', 'r') as n:
            self._blank_img = n.read().replace('\n', '').strip()

        if not (PATH/'page.conf').is_file():
            shutil.copy(self._data_path/'page.conf', PATH/'page.conf')
        self._conf_user = ConfFile(PATH/'page.conf')
        self._conf_page = ConfFile(self._data_path/'page.conf')

        self._icon_close = SvgIconToHTML('close').html

        self._set_nav_brand()
        self._set_nav_langs()
        self._set_nav_langs_index_redirection()
        self._set_nav_items()
        self._set_nav_items_active()
        self._set_indexes_content()
        self._clear()

    def _clear(self) -> None:
        for node in os.listdir(self._site_path):
            if os.path.isdir(self._site_path/node) and node not in self._langs:
                # shutil.rmtree(self._site_path/node)
                with open(self._html_path/'clear.html', 'r') as file_:
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

    def _conf(self, name: str, key: str) -> str:
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
        with open(self._html_path/'index.html', 'r') as file_:
            html = file_.read()
        return html.split('<!-- / -->')

    def _html_formatted_content(
            self, html: DocxHTML, start: str, end: str) -> DocxHTML:

        with open(self._html_path/'cover.html', 'r') as f:
            cover = f.read().replace('#image', self._noise_img)
            cover, cover_alt = cover.split('<!-- / -->')

        with open(self._html_path/'title.html', 'r') as f:
            title, title_alt = f.read().split('<!-- / -->')
        
        if not html.cover:
            cover = cover_alt
            title = title_alt

        html.start = start
        html.cover = cover.replace('#img', html.cover_src)
        html.title = title.replace('#title', html.title_text)
        html.end = end

        return html

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

    def _set_indexes_content(self) -> None:
        with open(self._html_path/'card.html', 'r') as f:
            card = f.read()

        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as f:
                start, end = f.read().split('<!-- CONTENT -->')

            content = ''
            for inode in os.listdir(self._docs_path/lang):
                if os.path.isfile(self._docs_path/lang/inode):
                    if not inode.endswith('.docx'):
                        continue

                    doc_name = inode.replace('.docx', '.html')
                    html = DocxHTML(self._docs_path/lang/inode)
                    html = self._html_formatted_content(html, start, end)
                    html.save(self._site_path/lang/doc_name)

                    if not html.cover_src: html.cover_src = self._blank_img
                    content += card.replace(
                        '#title', html.title_text).replace(
                        '#link', doc_name).replace(
                        '#img_src', html.cover_src).replace(
                        '#img_noise', self._noise_img)
                else:
                    self._set_index_content_4_categs(lang, inode, card)

            with open(self._site_path/lang/'index.html', 'w+') as f:
                f.write(f'{start}{content}{end}')

    def _set_index_content_4_categs(
            self, lang: str, page: str, card: str) -> None:
        content = ''
        with open(self._site_path/lang/page/'index.html', 'r') as f:
            start, end = f.read().split('<!-- CONTENT -->')

        with open(self._html_path/'categ.html', 'r') as f:
            categ_card = f.read()

        files = []
        dirs = []
        for inode in os.listdir(self._docs_path/lang/page):
            if os.path.isfile(self._docs_path/lang/page/inode):
                if inode.endswith('.docx'): files.append(inode)
            else:
                dirs.append(inode)

        if dirs:
            content += '<div class="m-5"> </div>\n'
            for num, inode in enumerate(dirs):
                padding = 'pe-4 ps-2'
                if num % 2 == 0:
                    padding = 'ps-4 pe-2'
                    content += '<div class="row m-0 p-0">\n'

                categ_name = inode.upper()
                content += categ_card.replace(
                    '#title', categ_name).replace(
                    '#link', inode + '/index.html').replace(
                    '#img_src', self._blank_img).replace(
                    '#img_noise', self._noise_img).replace(
                    '#padding', padding)

                if num % 2 != 0 or len(dirs) == 1:
                    content += '\n</div>\n'

                index_path = self._site_path/lang/page/inode/'index.html'
                index_path.parent.mkdir(parents=True, exist_ok=True)
                self._set_index_content_4_sub_categs(lang, page, inode, card)

        for inode in files:
            doc_name = inode.replace('.docx', '.html')
            html = DocxHTML(self._docs_path/lang/page/inode)
            html = self._html_formatted_content(html, start, end)
            html.save(self._site_path/lang/page/doc_name)

            if not html.cover_src: html.cover_src = self._blank_img
            content += card.replace(
                '#title', html.title_text).replace(
                '#link', doc_name).replace(
                '#img_src', html.cover_src).replace(
                '#img_noise', self._noise_img)

        with open(self._site_path/lang/page/'index.html', 'w') as f:
            f.write(f'{start}{content}{end}')

    def _set_index_content_4_sub_categs(
            self, lang: str, page: str, categ: str, card: str) -> None:
        content = ''
        with open(self._site_path/lang/page/'index.html', 'r') as f:
            html = f.read()

        html = self._update_nav_links(lang, html, 'SUB-CATEG')
        start, end = html.split('<!-- CONTENT -->')

        for inode in os.listdir(self._docs_path/lang/page/categ):
            if os.path.isfile(self._docs_path/lang/page/categ/inode):
                if not inode.endswith('.docx'):
                    continue
                
                doc_name = inode.replace('.docx', '.html')
                html = DocxHTML(self._docs_path/lang/page/categ/inode)
                html = self._html_formatted_content(html, start, end)
                html.save(self._site_path/lang/page/categ/doc_name)

                if not html.cover_src: html.cover_src = self._blank_img
                content += card.replace(
                    '#title', html.title_text).replace(
                    '#link', doc_name).replace(
                    '#img_src', html.cover_src).replace(
                    '#img_noise', self._noise_img)

        with open(self._site_path/lang/page/categ/'index.html', 'w') as f:
            f.write(f'{start}{content}{end}')

    def _set_nav_brand(self) -> None:
        name = ''
        if self._conf('Brand', 'display_name'):
            name = self._conf('Brand', 'name')

        logo = ''
        if self._conf('Brand', 'display_logo'):
            logo = (PATH/self._conf('Brand', 'logo')).as_posix()

        self._html_top = self._html_top.replace(
            '#brand', logo).replace(
                '#favicon', (PATH/self._conf('Brand', 'favicon')).as_posix()
            ).replace(
                '<!-- TAB TITLE-->', self._conf('Brand', 'name')
            ).replace(
                '<!-- PAGE NAME -->', name
            ).replace(
                '#LightSubtitleColor',
                self._conf('Post:LightTheme', 'subtitle_color')
            ).replace(
                '#DarkSubtitleColor',
                self._conf('Post:DarkTheme', 'subtitle_color'))

    def _set_nav_items(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                index = file_.read()

            li_itens = ''
            for node in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/node):
                    li_itens += """
                        <li class="nav-item m-0 p-0">
                         <a {} {} href="{}/index.html">{}</a>
                        </li>
                        """.replace(' '*24, ' '*5).format(
                            'aria-current="page"',
                            'class="m-0 mx-2 p-0 nav-link"', node, node)

            new_index = index.replace('<!-- NAV ITEM -->', li_itens)
            with open(self._site_path/lang/'index.html', 'w+') as f:
                f.write(new_index)

    def _set_nav_items_active(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                html = file_.read()

            html = self._update_nav_links(lang, html, 'CATEG')
            for inode in os.listdir(self._docs_path/lang):
                if os.path.isdir(self._docs_path/lang/inode):
                    path = self._site_path/lang/inode/'index.html'
                    path.parent.mkdir(parents=True, exist_ok=True)

                    link = re.findall(r'-link\" href=\"[^\"]+\">'+inode, html)
                    if link:
                        n = link[0].replace('-link', '-link active')
                        html = html.replace(link[0], n)

                    with open(path, 'w') as file_:
                        file_.write(html)

    def _set_nav_langs(self) -> None:
        with open(self._html_path/'langs.html', 'r') as f:
            lang_btn, lang_item = f.read().split('<!-- / -->')
            lang_btn = lang_btn.replace('\n', '').strip()
            lang_item = lang_item.replace('\n', '\n' + (' '*10))

        langs = ''
        for lang in self._langs:
            icon = lang.lower().split('-')[1] if '-' in lang else lang.lower()
            langs += lang_item.replace('#lang', lang).replace('#icon', icon)

        if len(self._langs) == 1:
            self._html_top = self._html_top.replace(lang_btn, '<span></span>')

        self._html_top = self._html_top.replace(
            '<!-- LANGS -->', langs).replace(
            '<!-- CLOSE ICON -->', self._icon_close)

    def _set_nav_langs_index_redirection(self) -> None:
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
