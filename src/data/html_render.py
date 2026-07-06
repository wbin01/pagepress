#!/usr/bin/env python3
import re
import base64

from zipfile import ZipFile
from lxml import etree
from .svg_icon_to_html import SvgIconToHTML


class DocxParser:
    pass


class HTMLRender(object):
    def __init__(self, docx_parser: DocxParser) -> None:
        # Args
        self._parser = docx_parser

        # Contents
        self._top = ''
        self._cover = ''
        self._cover_src = ''
        self._title = ''
        self._body = ''
        self._modals = ''
        self._end = ''
        self._html = ''

        self._icon_close = icon = SvgIconToHTML('close').html
        self._icon_book = icon = SvgIconToHTML('book').html

        self._set_html()

    @property
    def cover(self) -> str:
        return self._cover

    @property
    def cover_src(self) -> str:
        return self._cover_src

    @property
    def html(self) -> str:
        self._html += self._top
        self._html += self._body + '\n'
        self._html += self._modals
        self._html += self._end
        return self._html

    @property
    def html_body(self) -> str:
        return self._body

    @property
    def html_end(self) -> str: 
        return self._end

    @html_end.setter
    def html_end(self, html: str) -> None:
        self._end = html

    @property
    def html_modals(self) -> str:
        return self._modals

    @property
    def html_top(self) -> str:
        return self._top

    @html_top.setter
    def html_top(self, html: str) -> None:
        self._top = html

    @property
    def title(self) -> str:
        return self._title

    def save(self, path: str = '', html: str = None) -> None:
        path = path if path else self._parser.path
        path = path.as_posix().replace('.docx', '.html')

        html = html if html else self.html
        with open(path, 'w') as html:
            html.write(self._html)
    
    def _set_html(self) -> None:
        # Body
        self._body = ' <main>\n <article>\n\n'
        for parse in self._parser.parse['body']:
            self._body += self._set_html_body(parse)
        self._body +='\n </article>\n </main>\n\n <footer></footer>\n'

        # self._parser.print()
        for parse in self._parser.parse['comments']:
            self._modals += self._set_html_body(parse, True)

        # Start
        self._top = (
            '<!DOCTYPE html>\n'
            '<html>\n'
            ' <head>\n'
            f'  <title>{self._title}</title>\n'
            '  <meta charset="utf-8">\n'
            '  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/c'
            'ss/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjp'
            'PEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossor'
            'igin="anonymous">\n'
            '  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/'
            'js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNk'
            'mXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anony'
            'mous"></script>\n'
            '  <style>\n'
            '   h1, h2, h3, h4, h5, h6, h7, h8, h9 { color: #3770BC }'
            '   .post-title { color: #000000; font-size: 28pt; }\n'
            '   .bg { background-color: #F4C559; border-radius: 3px; }\n'
            '  </style>\n'
            ' </head>\n'
            ' <body>\n\n')

        # End
        self._end = f'\n </body>\n</html>'

        # self._html += self._top
        # self._html += self._body + '\n'
        # self._html += self._modals
        # self._html += self._end

    def _set_html_body(self, parse: dict, modal: bool = False) -> str:
            parse_tag = tag = pr = text = id_ = style = src = ''
            for key, value in parse.items():
                if key == 'tag':
                    parse_tag = value
                    tag = self._set_tag(value)

                elif key == 'pr' and value:
                    for pr_key, pr_value in value.items():
                        if tag == 'img' and pr_key == 'src': src = pr_value
                        pr += f' {pr_key}="{pr_value}"'

                elif key == 'children':
                    for run in value:
                        text += self._set_text_run(run)

                elif key == 'meta':
                    id_ = value['id']

                elif key == 'style':
                    style = value

            # End format
            if tag == 'h1' and parse_tag == 'Title':
                self._title = text

                class_ = 'post-title'
                if 'align' in style: class_ += f' text-' + style['align']
                class_ = f' class="{class_}"'

                tag = f'\n   <{tag}{class_}>{text}</{tag}>\n'
                tag = f'\n  <!-- Title -->\n  <header>{tag}  </header>\n\n'

            elif tag == 'div' and parse_tag == 'comment_modal':
                tag = (
                    f'  <!-- Modal {id_} -->\n'
                    f'  <div class="modal fade " id="modal{id_}" tabindex="-1" '
                    'aria-labelledby="#idLabel" aria-hidden="true" '
                    'data-bs-theme="read">\n'
                    '   <div class="modal-dialog modal-lg '
                    'modal-dialog-scrollable">\n'
                    '    <div class="modal-content">\n'
                    '     <div class="modal-body p-0 m-0">\n\n'
                    '      <div class="px-2 mt-2">\n'
                    f'       {text}\n'
                    '      </div>\n\n'
                    '      <div class="modal-footer p-0 m-1">\n'
                    '       <div class="d-grid gap-2 d-flex '
                    'justify-content-end">\n'
                    '        <button type="button" class="btn '
                    'btn-outline-danger btn-sm border border-0" '
                    'data-bs-dismiss="modal" aria-label="Close">\n'
                    f'         {self._icon_close}\n'
                    '        </button>\n'
                    '       </div>\n      </div>\n\n     </div>\n    </div>\n'
                    '   </div>\n  </div>\n')

            elif tag == 'img':
                class_ = styl = ''
                if 'align' in style: class_ = f'text-' + style['align']

                if 'max-width' in style:
                    styl = f' style="max-width:{style['max-width']};"'

                tag = (
                    f'  <figure class="image {class_}">\n   '
                    f'<{tag}{styl}{pr} />\n'
                    '   <figcaption></figcaption>\n'
                    '  </figure>\n')
                
                if not self._cover:
                    self._cover = tag
                    self._cover_src = src
                    tag = f'  <!-- Cover -->\n{tag}'
            else:
                class_ = ''
                if 'align' in style: class_ = f'text-' + style['align']
                if class_: class_ = f' class="{class_}"'

                tag = f'  <{tag}{class_}{pr}>{text}</{tag}>\n'

            return tag

    def _set_tag(self, value: str) -> str:
        tag = value
        if value == 'Title':
            tag, parse_tag = 'h1', value
        
        elif value == 'comment_modal':
            tag, parse_tag = 'div', value

        return tag

    def _set_text_run(self, run: dict) -> str:
        text = ''

        # Tag start
        for tag in run['tags']:
            if tag['tag'] == 'comment':
                text += ('<a type="button" class="ref_button '
                    'd-print-none" data-bs-toggle="modal" ')

            elif tag['tag'] == 'bg':
                text += '<span class="bg"'
            
            else:
                text += f'<{tag['tag']}'

            # Tag properties
            for pr_k, pr_v in tag['pr'].items():
                if tag['tag'] == 'comment':
                    text += f'data-bs-target="#modal{pr_v}"'
                else:
                    text += f' {pr_k}="{pr_v}"'
            text += '>'

        # Text
        if run['text'] == 'book':
            text += self._icon_book
        else:
            text += run['text']
        
        # Tag close - Reversed
        end_tags = []
        for tag in run['tags']:
            if tag['tag'] == 'comment':
                end_tags.append(f'</a>')

            elif tag['tag'] == 'bg':
                end_tags.append(f'</span>')
            
            else:
                end_tags.append(f'</{tag['tag']}>')

        end_tags.reverse()
        for end_tag in end_tags:
            text += end_tag

        return text


if __name__ == '__main__':
    from .docx_parser import DocxParser
    docx = DocxParser('/home/user/Documento1.docx')
    html = HTMLRender(docx)
    print(html._title)
    html.save()
