#!/usr/bin/env python3
import re
import hashlib
import locale
import shutil
import string
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
        self._name_chars = string.ascii_lowercase + string.digits
        self._items_per_page = 3

        self._clear()
        self._set_nav_brand()
        self._set_nav_langs()
        self._set_nav_langs_index_redirection()
        self._set_nav_items()
        self._set_nav_items_indexes()
        self._set_indexes_content()

    def _clear(self) -> None:
        for item in self._site_path.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

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

    def _langs_code(self) -> list:
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

    def _normalized_name(self, name: str, ext: str = '') -> str:
        if ext:
            if not ext.startswith('.'): ext = '.' + ext
            name = name[:-len(ext)]

        name, new_name = name.replace(' ', '-'), ''
        for char in name:
            char = char.lower()

            if char in self._name_chars or char == '-' or char == '_':
                new_name += char

            elif char in string.punctuation:
                for num, x in enumerate(string.punctuation):
                    if x == char: new_name += f'-{num}'
            else:
                new_name += '&'

        return new_name.replace('--', '-') + ext

    def _set_active_nav_item(self, page: str, html: str) -> str:
        link = re.findall(rf' nav-link\" href=\"[^\"]*\">{page}', html)
        if link:
            html = html.replace(
                link[0], link[0].replace(' nav-link', ' nav-link active'))
        return html

    def _set_html_page_item(
            self, html: DocxHTML, site_path: PATH, start: str, end: str,
            card: str, page: str = '') -> str:

        with open(self._html_path/'cover.html', 'r') as f:
            cover = f.read().replace('#image', self._noise_img)
            cover, cover_alt = cover.split('<!-- / -->')

        with open(self._html_path/'title.html', 'r') as f:
            title, title_alt = f.read().split('<!-- / -->')
        
        if not html.cover:
            cover = cover_alt
            title = title_alt

        if page:
            start = self._set_active_nav_item(page, start)
        
        html.start = start
        html.cover = cover.replace('#img', html.cover_src)
        html.title = title.replace('#title', html.title_text)
        html.end = end

        doc_name = html.path.name.replace('.docx', '.html')
        doc_name = self._normalized_name(doc_name, '.html')
        p = Path(self._site_path)
        html.save(site_path/doc_name)

        if not html.cover_src: html.cover_src = self._blank_img
        content = card.replace(
            '#title', html.title_text).replace(
            '#link', doc_name).replace(
            '#img_src', html.cover_src).replace(
            '#img_noise', self._noise_img)

        return content

    def _set_indexes_content(self) -> None:
        with open(self._html_path/'card.html', 'r') as f:
            card = f.read()

        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as f:
                start, end = f.read().split('<!-- CONTENT -->')

            pages, content, num, single_page = [], '', 0, False
            for inode in self._sorted(self._docs_path/lang):
                if (self._docs_path/lang/inode).is_file():
                    if single_page or not inode.endswith('.docx'):
                        continue
                    num += 1

                    html = DocxHTML(self._docs_path/lang/inode)
                    content += self._set_html_page_item(
                        html, self._site_path/lang, start, end, card)

                    if inode.startswith('*'):
                        single_page = True
                        html.save(self._site_path/lang/'index.html')

                    if num == self._items_per_page:
                        pages.append(content)
                        content, num = '', 0
                else:
                    self._set_index_content_4_categs(lang, inode, card)

            if single_page: continue
            if content and content not in pages: pages.append(content)
            for num, content in enumerate(pages):
                num += 1
                content = self._set_pagination(content, num, len(pages))

                if num == 1: num = ''
                with open(self._site_path/lang/f'index{num}.html', 'w+') as f:
                    f.write(f'{start}{content}{end}')

    def _set_index_content_4_categs(
            self, lang: str, page: str, card: str) -> None:
        content = ''
        page_ = self._normalized_name(page)
        with open(self._site_path/lang/page_/'index.html', 'r') as f:
            start, end = f.read().split('<!-- CONTENT -->')

        with open(self._html_path/'categ.html', 'r') as f:
            categ_card = f.read()

        dirs, docs = [], []
        for path in (self._docs_path/lang/page).iterdir():
            if path.is_file():
                if path.name.endswith('.docx'): docs.append(path.name)
            else:
                dirs.append(path.name)

        if dirs:
            content += '<div class="m-5"> </div>\n'
            for num, categ in enumerate(self._sorted(dirs, True)):
                inode_ = self._normalized_name(categ)
                padding = 'pe-4 ps-2'
                if num % 2 == 0:
                    padding = 'ps-4 pe-2'
                    content += '<div class="row m-0 p-0">\n'

                categ_name = re.sub(r'^\d+ +-|^\d+-|^\d+ ', '', categ.upper())
                content += categ_card.replace(
                    '#title', categ_name).replace(
                    '#link', inode_ + '/index.html').replace(
                    '#img_src', self._blank_img).replace(
                    '#img_noise', self._noise_img).replace(
                    '#padding', padding)

                if num % 2 != 0 or len(dirs) == 1:
                    content += '\n</div>\n'
                
                index_path = self._site_path/lang/page_/inode_/'index.html'
                index_path.parent.mkdir(parents=True, exist_ok=True)
                self._set_index_content_4_sub_categs(lang, page, categ, card)

        pages, num, single_page = [], 0, False
        for doc in self._sorted(docs):
            if single_page: continue

            num += 1
            html = DocxHTML(self._docs_path/lang/page/doc)
            content += self._set_html_page_item(
                html, self._site_path/lang/page_, start, end, card, page)

            if doc.startswith('*'):
                single_page = True
                html.save(self._site_path/lang/page_/'index.html')

            if num == self._items_per_page:
                pages.append(content)
                content, num = '', 0

        if single_page: return
        if content and content not in pages: pages.append(content)
        for num, content in enumerate(pages):
            num += 1
            content = self._set_pagination(content, num, len(pages))

            if num == 1: num = ''
            with open(self._site_path/lang/page_/f'index{num}.html', 'w') as f:
                start = self._set_active_nav_item(page, start)
                f.write(f'{start}{content}{end}')

    def _set_index_content_4_sub_categs(
            self, lang: str, page: str, categ: str, card: str) -> None:
        page_ = self._normalized_name(page)
        categ_ = self._normalized_name(categ)
        content = ''
        with open(self._site_path/lang/page_/'index.html', 'r') as f:
            html = f.read()

        html = self._update_nav_links(lang, html, 'SUB-CATEG')
        start, end = html.split('<!-- CONTENT -->')

        items = self._docs_path/lang/page/categ
        if not any(items.iterdir()):
            with open(self._site_path/lang/page_/categ_/'index.html','w') as f:
                start = self._set_active_nav_item(page, start)
                f.write(f'{start}{content}{end}')
                return

        pages, content, num, single_page = [], '', 0, False
        for inode in self._sorted(items):
            if (items/inode).is_file():
                if single_page: break
                if not inode.endswith('.docx'):
                    continue
                num += 1

                html = DocxHTML(self._docs_path/lang/page/categ/inode)
                content += self._set_html_page_item(html,
                    self._site_path/lang/page_/categ_, start, end, card, page)

                if inode.startswith('*'):
                    single_page = True
                    html.save(self._site_path/lang/page_/categ_/'index.html')

                if num == self._items_per_page:
                    pages.append(content)
                    content, num = '', 0

        if single_page: return
        if content and content not in pages: pages.append(content)
        for num, content in enumerate(pages):
            num += 1
            content = self._set_pagination(content, num, len(pages))

            if num == 1: num = ''
            with open(self._site_path/lang/page_/categ_/f'index{num}.html', 'w'
                    ) as f:
                start = self._set_active_nav_item(page, start)
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
            ).replace('<!-- TAB TITLE-->', self._conf('Brand', 'name')
            ).replace('<!-- PAGE NAME -->', name
            ).replace('#LightSubtitleColor',
                self._conf('Post:LightTheme', 'subtitle_color')
            ).replace('#DarkSubtitleColor',
                self._conf('Post:DarkTheme', 'subtitle_color'))

    def _set_nav_items(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                index = file_.read()

            li_itens, langs = '', self._docs_path/lang
            for node in self._sorted(langs, True):
                node_ = self._normalized_name(node)
                if (langs/node).is_dir():
                    li_itens += """
                        <li class="nav-item m-0 p-0">
                         <a {} {} href="{}/index.html">{}</a>
                        </li>
                        """.replace(' '*24, ' '*5).format(
                            'aria-current="page"',
                            'class="m-0 mx-2 p-0 nav-link"',
                            node_,
                            re.sub(r'^\d+ +-|^\d+-|^\d+ ', '', node))

            new_index = index.replace('<!-- NAV ITEM -->', li_itens)
            with open(self._site_path/lang/'index.html', 'w+') as f:
                f.write(new_index)

    def _set_nav_items_indexes(self) -> None:
        for lang in self._langs:
            with open(self._site_path/lang/'index.html', 'r') as file_:
                html = file_.read()

            html = self._update_nav_links(lang, html, 'CATEG')
            for path in (self._docs_path/lang).iterdir():
                categ = self._normalized_name(path.name)
                if path.is_dir():
                    path = self._site_path/lang/categ/'index.html'
                    path.parent.mkdir(parents=True, exist_ok=True)

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

    def _set_pagination(self, html: str, num: int, pages: int) -> str:
        with open(self._html_path/'pagination.html') as f:
            pag_min, pag_simple, pag_full = f.read().split('<!-- / -->')

        if pages == 1:
            control = ''
        elif pages == 2:
            control = pag_min
        elif pages <= 3:
            control = pag_simple
        else:
            control = pag_full

        if pages == 2:
            p1, p2, p3 = 1, 2, 3
        elif num <= 2:
            p1, p2, p3 = 1, 2, 3
        elif num == pages:
            p1, p2, p3 = num - 2, num - 1, num
        elif 2 < num <= pages:
            p1, p2, p3 = num - 1, num, num + 1

        next_, prev = num + 1, num -1
        if prev == 1 or num == 1: prev = ''
        if num == pages: next_ = pages
        
        if p1 == num:
            control = control.replace('-body">#P1', '-body active">#P1')
        elif p2 == num:
            control = control.replace('-body">#P2', '-body active">#P2')
        else:
            control = control.replace('-body">#P3', '-body active">#P3')

        control = control.replace(
            '#P1', f'{p1}').replace('#P2', f'{p2}').replace('#P3', f'{p3}')

        if p1 == 1: p1 = ''
        control = control.replace(
            '#p1', f'index{p1}.html').replace(
            '#p2', f'index{p2}.html').replace(
            '#p3', f'index{p3}.html').replace(
            '#next', f'index{next_}.html').replace(
            '#prev', f'index{prev}.html').replace(
            '#last', f'index{pages}.html').replace(
            '#first', f'index.html').replace(
            '#NUM', str(num)).replace('#PAGES', str(pages))

        html += control
        return html

    def _sorted(self, str_list: list | Path, is_dirs: bool = False) -> list:
        if isinstance(str_list, Path):
            str_list = [x.name for x in str_list.iterdir()]
        
        alphas, ints = [], []
        for item in str_list:
            
            item = item.strip()

            num = re.findall(r'^\d+\.\d|^\d+', item)
            if num:
                num = float(num[0]) if '.' in num[0] else int(num[0])
                ints.append((num, item))
            else:
                alphas.append((item.lower(), item))

        end = []
        for item in sorted(ints):
            end.append(item[1])
        for item in sorted(alphas):
            end.append(item[1])

        return end if is_dirs else reversed(end) 

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
        for path in (self._docs_path/lang).iterdir():
            if path.is_dir():
                page_name = self._normalized_name(path.name)
                html = html.replace(
                    f'href="{pages_prev}{page_name}/index.html"',
                    f'href="{pages_next}{page_name}/index.html"')
        return html


if __name__ == '__main__':
    pass
