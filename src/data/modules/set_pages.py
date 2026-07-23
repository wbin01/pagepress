#!/usr/bin/env python3
import re
import shutil
import string
from pathlib import Path

from .conf import Conf
from .docx_html import DocxHTML
from .img import Img

PATH = Path(__file__).resolve().parent.parent.parent


class SetPages(object):
    def __init__(self) -> None:
        self._conf = Conf()
        self._img = Img()

        self._path_docs = self._conf.path_docs
        self._path_site = self._conf.path_site
        self._path_data = self._conf.path_data
        self._path_html = self._conf.path_html

        noise = 'noise.txt'
        if not self._conf.user('Category:Cover', 'noise'): noise = 'no.txt'
        self._img_noise = self._img.base64(self._path_data/'img64'/noise)
        self._img_blank = self._img.base64(self._path_data/'img64'/'blank.txt')

        cover = self._html_base('cover').replace('#image', self._img_noise)
        title = self._html_base('title')
        self._html_cover, self._html_cover_alt = cover.split('<!-- / -->')
        self._html_title, self._html_title_alt = title.split('<!-- / -->')
        self._html_categ_title = self._html_base('categ-title')
        self._html_top, self._html_end = self._html_base()
        self._html_card = self._html_base('card')

        self._name_chars = string.ascii_lowercase + string.digits
        self._items_per_page = 3

        self._all_last_doc_paths = []
        self._all_doc_paths = []
        self._all_docs = {}

        self._clear()
        self._nav_brand()
        self._nav_langs()
        self._nav_redirection()
        self._nav_items()
        self._home_pages()
        self._pages_content()

    def _clear(self) -> None:
        for item in self._path_site.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def _get_cover_image(self, path: Path) -> str:
        image = ''
        for i in path.iterdir():
            if i.is_file() and i.suffix.lower() in self._img.supported_ext:
                image = self._img.base64(i)
                break
        return image

    def _get_html_card_cover(self, categ: str, image: str) -> str:
        with open(self._path_html/'categ.html', 'r') as f:
            categ_card, categ_card_alt = f.read().split('<!-- / -->')

        categ = self._name_for_display(categ).upper()
        key = 'Category:Cover'
        if image:
            html_title = categ_card
            if not self._conf.user(key, 'title-shadow'):
                categ_card = categ_card.replace(
                    'text-shadow: 2px 2px 5px #000;', '')

            text_color = self._conf.user(key, 'title-color')
            if text_color == 'dark':
                categ_card = categ_card.replace('text-light', 'text-dark')

            elif text_color == 'auto':
                categ_card = categ_card.replace('text-light', 'text-body')

            elif text_color != 'light':
                categ_card = categ_card.replace(
                    'style="', f'style="color:{text_color};')

            if not self._conf.user(key, 'shadow'):
                categ_card = categ_card.replace(
                    'background: #000000; background: linear-gradient(0deg, '
                    '#00000080 0%, #00000040 30%, #00000005 80%);', '')

            if not self._conf.user(key, 'display-title'):
                categ = ''
                categ_card = categ_card.replace(
                    'text-shadow: 2px 2px 5px #000;', '')
                categ_card = categ_card.replace(
                    'background: #000000; background: linear-gradient(0deg, '
                    '#00000080 0%, #00000040 30%, #00000005 80%);', '')

        categ_card = categ_card.replace('#title', categ)
        categ_card_alt = categ_card_alt.replace('#title', categ)
        return categ_card, categ_card_alt

    def _get_html_cover(self, categ: str, sub_categ: str, image: str) -> str:
        clss = 'container text-center fw-light text-body text-opacity-25 mt-2'
        categ = self._name_for_display(categ).upper()
        title = ''
        if sub_categ:
            categ = f'<small>{categ} / </small>'
            categ = f'<small class="text-opacity-5 fs-6">{categ}</small>'
            sub_categ = self._name_for_display(sub_categ).upper()
            categ = categ + sub_categ
            title = f'<h3 class="{clss}">{categ}</h3>\n'
        cover = ''

        key = 'Category:Cover'
        if image:
            html_title = self._html_categ_title
            if not self._conf.user(key, 'title-shadow'):
                html_title = html_title.replace(
                    'text-shadow: 2px 2px 5px #000;', '')

            text_color = self._conf.user(key, 'title-color')
            if text_color == 'dark':
                html_title = html_title.replace('text-light', 'text-dark')

            elif text_color == 'auto':
                html_title = html_title.replace('text-light', 'text-body')

            elif text_color != 'light':
                html_title = html_title.replace(
                    'style="', f'style="color:{text_color};')

            if not self._conf.user(key, 'shadow'):
                html_title = html_title.replace(
                    'background: #000000; background: linear-gradient(0deg, '
                    '#00000080 0%, #00000040 60%, #00000005 100%);', '')

            if not self._conf.user(key, 'display-title'):
                categ = ''
                html_title = html_title.replace(
                    'text-shadow: 2px 2px 5px #000;', '')
                html_title = html_title.replace(
                    'background: #000000; background: linear-gradient(0deg, '
                    '#00000080 0%, #00000040 60%, #00000005 100%);', '')

            html_title = html_title.replace('#title', categ)
            html_cover = self._html_cover.replace('#img', image)
            html_cover = html_cover.replace('height:300px;', 'height:150px;')
            cover = f'{html_cover}\n{html_title}'
            return cover
        return title

    def _home_pages(self) -> None:
        for lang in self._conf.langs:
            with open(self._path_site/lang/'index.html', 'r') as file_:
                html = file_.read()

            html = self._update_nav_links(lang, html, 'CATEG')
            for path in (self._path_docs/lang).iterdir():
                categ = self._name_for_url(path.name)
                if path.is_dir():
                    path = self._path_site/lang/categ/'index.html'
                    path.parent.mkdir(parents=True, exist_ok=True)

                    with open(path, 'w') as file_:
                        file_.write(html)

    def _html_base(self, path: str = '') -> list:
        path = self._path_html/f'{path}.html'
        if path.is_file():
            with open(path, 'r') as f: return f.read()

        with open(self._path_html/'index.html', 'r') as file_:
            html = file_.read()
        return html.split('<!-- / -->')

    def _index_items(self, lang) -> list:
        data_paths = self._path_data/f'{lang}-paths.txt'
        if not data_paths.is_file():
            with open(data_paths, 'w+') as f: f.write('')

        with open(data_paths, 'r') as f:
            all_last_doc_paths = f.read().split('\n')

        news, olds = [], []
        for html in self._all_docs[lang]:
            if html.path.as_posix() in all_last_doc_paths:
                olds.append(html)
            else:
                news.append(html)

        lasts = []
        for item in all_last_doc_paths:
            for x in olds:
                if x.path.as_posix() == item: lasts.append(x)

        news.extend(lasts)
        with open(data_paths, 'w+') as f:
            f.write('\n'.join([x.path.as_posix() for x in news]))

        return news

    def _name_for_display(self, name: str) -> str:
        return re.sub(r'^\d+ +-|^\d+-|^\d+ ', '', name)

    def _name_for_url(self, name: str, ext: str = '') -> str:
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

    def _nav_brand(self) -> None:
        name = self._conf.user('Brand', 'name')
        logo = (PATH/self._conf.user('Brand', 'logo')).as_posix()
        favicon = (PATH/self._conf.user('Brand', 'favicon')).as_posix()
        light_subtitle = self._conf.user('Post:LightTheme', 'subtitle-color')
        dark_subtitle = self._conf.user('Post:DarkTheme', 'subtitle-color')

        self._html_top = self._html_top.replace(
            '#brand', logo).replace(
            '#favicon', favicon).replace(
            '<!-- TAB TITLE-->', name).replace(
            '<!-- PAGE NAME -->', name).replace(
            '#LightSubtitleColor', light_subtitle).replace(
            '#DarkSubtitleColor', dark_subtitle)

    def _nav_items(self) -> None:
        a = '<a aria-current="page" class="m-0 mx-1 p-0 px-1 nav-link" #>*</a>'
        li = f'<li class="nav-item m-0 p-0">{a}</li>\n     '
        for lang in self._conf.langs:
            with open(self._path_site/lang/'index.html', 'r') as file_:
                index = file_.read()

            li_itens = ''
            for node in self._sorted(self._path_docs/lang, True):
                node_ = self._name_for_url(node)
                if (self._path_docs/lang/node).is_dir():
                    li_itens += li.replace(
                        '#', f'href="{node_}/index.html"').replace(
                        '*', self._name_for_display(node))

            new_index = index.replace('<!-- NAV ITEM -->', li_itens.strip())
            with open(self._path_site/lang/'index.html', 'w+') as f:
                f.write(new_index)

    def _nav_langs(self) -> None:
        with open(self._path_html/'langs.html', 'r') as f:
            lang_btn, lang_item = f.read().split('<!-- / -->')
            lang_btn = lang_btn.replace('\n', '').strip()
            lang_item = lang_item.replace('\n', '\n' + (' '*10))

        langs = ''
        for lang in self._conf.langs:
            icon = lang.lower().split('-')[1] if '-' in lang else lang.lower()
            langs += lang_item.replace('#lang', lang).replace('#icon', icon)

        if len(self._conf.langs) == 1:
            self._html_top = self._html_top.replace(lang_btn, '<span></span>')

        self._html_top = self._html_top.replace(
            '<!-- LANGS -->', langs).replace(
            '<!-- CLOSE ICON -->', self._img.icon('close'))

    def _nav_redirection(self) -> None:
        index_start = self._html_top.replace(
            '<html lang="en-US"',
            f'<html lang="{self._conf.default_lang}"').replace(
            '// REDIRECT',
            "window.location.replace(`${savedLang}/index.html`);").replace(
            '#BRAND', 'index.html')

        with open(self._path_site/'index.html', 'w+') as index:
            index.write(index_start)
            index.write(self._html_end)

        for lang in self._conf.langs:
            file_path = self._path_site/lang/'index.html'
            file_path.parent.mkdir(parents=True, exist_ok=True)

            html_start = self._html_top.replace(
                '<html lang="en-US"', f'<html lang="{lang}"').replace(
                '#BRAND', f'../{lang}/index.html')

            with open(file_path, 'w+') as index:
                index.write(html_start + '\n<!-- CONTENT -->')
                index.write(self._html_end)

    def _pages_content(self) -> None:
        for lang in self._conf.langs:
            self._all_docs[lang] = []

        # Items
        for lang in self._conf.langs:
            doc_path = self._path_docs/lang
            site_path = self._path_site/lang

            with open(site_path/'index.html', 'r') as f:
                start, end = f.read().split('<!-- CONTENT -->')
            single = self._single_page(doc_path, site_path, start, end)

            items = []
            for inode in self._sorted(doc_path):
                if (doc_path/inode).is_file():
                    if single or not inode.endswith('.docx'):
                        continue
                    html = DocxHTML(doc_path/inode)
                    html = self._update_html(html, site_path, start, end)
                    items.append(html)
                else:
                    self._pages_categ_content(lang, inode)
            self._all_docs[lang].extend(items)

        # INDEX
        if single: return
        for lang in self._conf.langs:
            with open(self._path_site/lang/'index.html', 'r') as f:
                start, end = f.read().split('<!-- CONTENT -->')
            
            pages, content, num = [], '', 0
            for html in self._index_items(lang):
                content += self._update_card(html)

                num += 1
                if num == self._items_per_page:
                    pages.append(content)
                    content, num = '', 0

            if content and content not in pages:
                pages.append(content)

            for num, content in enumerate(pages):
                num += 1
                content = self._pagination(content, num, len(pages))

                if num == 1: num = ''
                with open(self._path_site/lang/f'index{num}.html', 'w+') as f:
                    f.write(f'{start}{content}{end}')

        self._all_last_doc_paths = self._all_doc_paths

    def _pages_categ_content(self, lang: str, page: str) -> None:
        content = ''
        page_ = self._name_for_url(page)
        doc_path = self._path_docs/lang/page
        site_path = self._path_site/lang/page_

        with open(site_path/'index.html', 'r') as f:
            start, end = f.read().split('<!-- CONTENT -->')

        # with open(self._path_html/'categ.html', 'r') as f:
        #     categ_card, categ_card_alt = f.read().split('<!-- / -->')

        if self._single_page(doc_path, site_path, start, end, page):
            return

        dirs, docs = [], []
        for path in doc_path.iterdir():
            if path.is_file():
                if path.name.endswith('.docx'): docs.append(path.name)
            else:
                dirs.append(path.name)

        if dirs:
            content += '<div class="m-0 p-0 mt-3"></div>\n'
            for num, categ in enumerate(self._sorted(dirs, True)):
                inode_ = self._name_for_url(categ)
                if num % 2 == 0:
                    content += '<div class="row m-0 p-0 mx-3">\n'

                cover_img = self._get_cover_image(doc_path/categ)
                categ_card, categ_card_alt = self._get_html_card_cover(categ, cover_img)
                card = categ_card if cover_img else categ_card_alt
                content += card.replace(
                    '#title', self._name_for_display(categ.upper())).replace(
                    '#link', inode_ + '/index.html').replace(
                    '#img_src', cover_img).replace(
                    '#img_noise', self._img_noise)

                if num % 2 != 0 or len(dirs) == 1 or num == len(dirs) - 1:
                    content += '\n</div>\n'
                
                index_path = site_path/inode_/'index.html'
                index_path.parent.mkdir(parents=True, exist_ok=True)

                self._pages_sub_categ_content(lang, page, categ, cover_img)

        pages, num, items = [], 0, []
        for doc in self._sorted(docs):
            html = DocxHTML(doc_path/doc)
            html = self._update_html(html, site_path, start, end, [page])
            items.append(html)
            content += html.card

            num += 1
            if num == self._items_per_page:
                pages.append(content)
                content, num = '', 0
        if content and content not in pages:
            pages.append(content)

        image = self._get_cover_image(doc_path)
        start += self._get_html_cover(page, '', image)
        for num, content in enumerate(pages):
            num += 1
            content = self._pagination(content, num, len(pages))

            if num == 1: num = ''
            with open(site_path/f'index{num}.html', 'w') as f:
                start = self._update_nav_active_item([page], start)
                f.write(f'{start}{content}{end}')

        self._all_docs[lang].extend(items)

    def _pages_sub_categ_content(
            self, lang: str, page: str, categ: str, image: str) -> None:
        page_ = self._name_for_url(page)
        categ_ = self._name_for_url(categ)
        doc_path = self._path_docs/lang/page/categ
        site_path = self._path_site/lang/page_/categ_

        with open(self._path_site/lang/page_/'index.html', 'r') as f:
            html = f.read()

        html = self._update_nav_links(lang, html, 'SUB-CATEG')
        start, end = html.split('<!-- CONTENT -->')

        if self._single_page(doc_path, site_path, start, end, page):
            return

        content = self._get_html_cover(page, categ, image)
        if not any(doc_path.iterdir()):
            with open(site_path/'index.html','w') as f:
                start = self._update_nav_active_item([page], start)
                f.write(f'{start}{content}{end}')
                return

        pages, num, items = [], 0, []
        for inode in self._sorted(doc_path):
            if (doc_path/inode).is_file():
                if not inode.endswith('.docx'):
                    continue
                
                html = DocxHTML(doc_path/inode)
                html = self._update_html(
                    html, site_path, start, end, [page, categ])
                items.append(html)
                content += html.card

                num += 1
                if num == self._items_per_page:
                    pages.append(content)
                    content, num = '', 0

        if content and content not in pages: pages.append(content)
        for num, content in enumerate(pages):
            num += 1
            content = self._pagination(content, num, len(pages))

            if num == 1: num = ''
            with open(site_path/f'index{num}.html', 'w') as f:
                start = self._update_nav_active_item([page], start)
                f.write(f'{start}{content}{end}')

        self._all_docs[lang].extend(items)

    def _pagination(self, html: str, num: int, pages: int) -> str:
        with open(self._path_html/'pagination.html') as f:
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
        
        active = 'active bg-secondary bg-opacity-50'
        if p1 == num:
            control = control.replace('-body">#P1', f'-body {active}">#P1')
        elif p2 == num:
            control = control.replace('-body">#P2', f'-body {active}">#P2')
        else:
            control = control.replace('-body">#P3', f'-body {active}">#P3')

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

    def _single_page(
            self, doc_path: PATH, site_path: PATH, start: str, end: str,
            page: str = '') -> bool:
        single = [x for x in doc_path.iterdir() if x.name.startswith('*')]
        if single:
            html = DocxHTML(single[0])
            self._update_html(html, site_path, start, end, [page], True)
        return single

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

    def _update_card(self, html) -> str:
        categ = ''
        if html.categ and html.categ[0]:
            style = (
                'class="m-0 p-0 px-2 fw-light position-absolute top-0 end-0 '
                'text-body text-opacity-75"')
            c0 = self._name_for_display(html.categ[0].upper())
            categ = f'<div {style}>{c0}</div>'

            if len(html.categ) == 2:
                small = f'<small><small class="text-body text-opacity-50">'
                c0 = c0.lower() + ' / '
                c1 = self._name_for_display(html.categ[1].upper())
                categ = f'<div {style}>{small}{c0}</small></small>{c1}</div>'

        card = html.card
        card = card.replace(
            f'<a class="text-decoration-none" href="{html.name}">',
            f'<a class="text-decoration-none" href="{html.link}">'
            ).replace('<!-- card title -->', categ)

        return card

    def _update_html(
            self, html: DocxHTML, site_path: PATH, start: str, end: str,
            categ: list = [], single: bool = False) -> str:
        
        cover, title = self._html_cover, self._html_title
        if not html.cover:
            cover, title = self._html_cover_alt, self._html_title_alt

        categs = ''
        if categ:
            start = self._update_nav_active_item(categ, start)
            if len(categ) == 2:
                style, small = (
                    ' class="container-lg m-0 p-0 fw-light text-opacity-75"',
                    '<small><small class="text-body text-opacity-50">')
                c0 = self._name_for_display(categ[0].lower()) + ' / '
                c1 = self._name_for_display(categ[1].upper())
                categs = f'<div{style}>{small}{c0}</small></small>{c1}</div>'
        
        cover = cover.replace('<!-- LABEL -->', categs)
        html.start = start
        html.cover = cover.replace('#img', html.cover_src)
        html.title = title.replace('#title', html.title_text)
        html.end = end

        doc_name = html.path.name.replace('.docx', '.html')
        doc_name = self._name_for_url(doc_name, '.html')
        if single: doc_name = 'index.html'

        site_path = site_path/doc_name
        site_path.parent.mkdir(parents=True, exist_ok=True)
        html.save(site_path)

        if not html.cover_src: html.cover_src = self._img_blank
        content = self._html_card.replace(
            '#categs', categs).replace(
            '#title', html.title_text).replace(
            '#link', doc_name).replace(
            '#img_src', html.cover_src).replace(
            '#img_noise', self._img_noise)

        link = site_path.as_posix().replace(self._path_site.as_posix(), '')[1:]
        html.card = content
        html.categ = categ
        html.name = doc_name
        html.link = link.split('/', maxsplit=1)[1]

        return html

    def _update_nav_active_item(self, categ: list, html: str) -> str:
        categ = re.sub(r'^\d+ +-|^\d+-|^\d+ ', '', categ[0])
        link = re.findall(rf' nav-link\" href=\"[^\"]*\">{categ}', html)
        if link:
            html = html.replace(
                link[0], link[0].replace(' nav-link', ' nav-link active'))
        return html

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
        for l in self._conf.langs:
            html = html.replace(
                f"""changeLang('{l}')" href="{langs_prev}{l}/index.html">""",
                f"""changeLang('{l}')" href="{langs_next}{l}/index.html">""")

        # Pages link
        for path in (self._path_docs/lang).iterdir():
            if path.is_dir():
                page_name = self._name_for_url(path.name)
                html = html.replace(
                    f'href="{pages_prev}{page_name}/index.html"',
                    f'href="{pages_next}{page_name}/index.html"')
        return html


if __name__ == '__main__':
    pass
