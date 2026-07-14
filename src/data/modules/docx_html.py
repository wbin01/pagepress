#!/usr/bin/env python3
import re

from markdown import markdown

from docx_parse import DocxParse
from svg_icon_to_html import SvgIconToHTML

HTML_START = """
<!DOCTYPE html>
<html>
 <head>
  <title>#TITLE</title>
  <meta charset="utf-8">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.*
min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYm*
Dr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.*
bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9*
GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
  <style>
   h1, h2, h3, h4, h5, h6, h7, h8, h9 { color: #3770BC }
   .post-title { color: #000000; font-size: 28pt; }
   .bg { background-color: #F4C559; border-radius: 3px; }
  </style>
 </head>
 <body>
"""

MODAL_START = """
  <!-- Modal #MODAL_ID -->
  <div class="modal fade modal-text" id="modal#MODAL_ID" tabindex="-1" *
aria-labelledby="#idLabel" aria-hidden="true" data-bs-theme="read">
   <div class="modal-dialog modal-lg modal-dialog-scrollable">
    <div class="modal-content">
     <div class="modal-body p-0 m-0">
      <div class="px-2 mt-2">
"""

MODAL_END = """
      </div>
      <div class="p-0 m-1">
       <div class="d-grid gap-2 d-flex justify-content-end">
        <button type="button" class="btn btn-outline-danger m-2 btn-sm border *
border-0" data-bs-dismiss="modal" aria-label="Close">
         #ICON_CLOSE
        </button>
       </div>
      </div>
     </div>
    </div>
   </div>
  </div>
"""

HTML_END = """
  <footer></footer>
 </body>
</html>
"""


class DocxHTML(object):
    """..."""
    def __init__(self, path: str, img_base64: bool = False) -> None:
        """..."""
        self._parser = DocxParse(path, img_base64)
        self._map = self._get_map()

        self._icon_close = SvgIconToHTML('close').html
        self._icon_book = SvgIconToHTML('book').html
        self._icon_plus_ref = SvgIconToHTML('plus-ref').html

        self._cover = None
        self._title = None
        self._body = self._set_body()
        self._modals = self._set_modals()
        self._html = None

    @property
    def html(self) -> str:
        """..."""
        html = HTML_START
        html += self._body
        html += self._modals
        html += HTML_END
        self._html = html.replace('*\n', '').strip()
        return self._html

    def save(self, path: str = '', html: str = None) -> None:
        """..."""
        if not path:
            path = self._parser.path

        path = path.replace('.docx', '.html')
        html = html if html else self._html

        if not html:
            if not self._html: self.html
            html = self._html

        with open(path, 'w') as f:
            f.write(html)

    @staticmethod
    def _markdown_to_html(text: str) -> str:
        details = re.findall(r'<p>&gt;[^&]+&lt;</p>', text)
        if details:
            for detail in details:
                open_ = ''
                summary = content = ''
                header = re.findall(r'<p>&gt;[^<]+</p>', detail)
                if header:
                    content = detail.replace(header[0], '')
                    content = content.replace('&gt;', '').replace('&lt;', '')

                    summary = header[0].replace('<p>', '').replace('</p>', '')
                    summary = summary.replace('&gt;', '').replace('&lt;', '')
                    if summary.strip().startswith('*'):
                        open_ = '_OPEN'
                        summary = summary.strip().strip('*').strip()
                
                text = text.replace(
                    detail,
                    f'!DETAIL{open_}!SUMMARY{summary}SUMMARY!{content}DETAIL!')

        verses = re.findall(r'v\d+ ', text)
        if verses:
            for verse in verses:
                text = text.replace(verse, f'!VERSE{verse[1:]}VERSE!')

        text = markdown(text).replace(
            '!DETAIL_OPEN', f'\n<details open>\n').replace(
            '!DETAIL', f'\n<details>\n').replace(
            'DETAIL!', '\n</details>\n').replace(
            '!SUMMARY', '\n<summary>').replace(
            'SUMMARY!', '</summary>\n').replace(
            '!VERSE', '<small class="verse">\n').replace(
            'VERSE!', '</small>')

        return f'\n{text}\n'

    def _set_body(self) -> str:
        body = ''
        for line in self._parser.parse['document']:
            tag_start = '  <' + self._map[line.type]

            align = ''
            if 'text-align' in line.styles:
                align = f'text-{line.styles["text-align"]}'
            
            if line.classes or align:
                if line.classes: align += ' '
                tag_start += f' class="{align}{' '.join(line.classes)}"'

            if line.properties:
                for key, value in line.properties.items():
                    tag_start += f' {key}="{value}"'
            
            if line.styles:
                tag_start += ' style="'
                for key, value in line.styles.items():
                    if key != 'text-align':
                        tag_start += f'{key}: {value}; '
                tag_start += '"'
            tag_start = tag_start.replace(' style=""', '')

            tag_start += '>'
            content = self._set_body_runs(line)
            tag_end = f'</{self._map[line.type]}>\n'

            tag = tag_start + content + tag_end
            body += tag.replace(' "', '"')

        return body

    def _set_body_runs(self, line) -> str:
        content = ''
        for run in line.runs:
            text = run.text

            tag_start = ''
            for t in run.tags:
                tag_start += '<' + t['tag']
                tag_start += ''.join(
                    [f' {key}="{value}"' for key, value in t.items()
                    if key != 'tag'])
                tag_start += '>'

                if 'comment-button' in t.values():
                    if run.text == 'book':
                        text = self._icon_book
                    elif run.text == '+':
                        text = self._icon_plus_ref

                    tag_start = tag_start.replace(
                        'comment-button',
                        'comment-button text-decoration-none d-print-none')

            if run.type == 'Image':
                src = run.properties['src']
                width = run.properties['width']
                height = run.properties['height']
                align = ''
                if 'text-align' in line.styles:
                    align = f' class="text-{line.styles["text-align"]}"'

                img = f'<img width="{width}" height="{height}" src="{src}">'
                tag_start += f'<figure{align}>{img}</figure>'

            elif run.type == 'Draw':
                pass

            content += tag_start + text

            tag_end = ''
            for t in run.tags:
                tag_end += f'</{t['tag']}>'

            content += tag_end

        return content

    def _set_modals(self) -> str:
        modals = ''
        for line in self._parser.parse['comments']:
            if not line.properties:
                continue

            tag_start = MODAL_START.replace('#MODAL_ID', line.properties['id'])

            text = ''
            for run in line.runs:
                text += f'<p>{run.text}</p>'
            text = self._markdown_to_html(text).replace('\n', '\n       ')

            tag_end = MODAL_END.replace('#ICON_CLOSE', self._icon_close)

            tag = tag_start + text + tag_end
            modals += tag.replace(' "', '"')
        
        return modals

    @staticmethod
    def _get_map():
        tags_map = {f'Heading {x}': f'h{x}' for x in range(1, 10)}
        tags_map.update({
            'Quote': 'blockquote', 'Paragraph': 'p', 'Title': 'h1',
            'Comment': 'div',
            })
        return tags_map

if __name__ == '__main__':
    html = DocxHTML('~/doc.docx', img_base64=True)
    html.save()
