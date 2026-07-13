#!/usr/bin/env python3
from docx_parse import DocxParse


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
  <!-- Modal #ID -->
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
    def __init__(self, path: str) -> None:
        """..."""
        self._parser = DocxParse(path)

        self._cover = None
        self._title = None
        self._body = None
        self._modals = None
        self._html = None

        self._map = self._get_map()
        self._set_html()

    @property
    def html(self) -> str:
        """..."""
        html = HTML_START
        html += self._body
        html += HTML_END
        html = html.replace('*\n', '').strip()
        print(html)
        return html

    def save(self, path: str = '', html: str = None) -> None:
        """..."""
        if not path:
            path = self._parser.path

        path = path.replace('.docx', '.html')
        html = html if html else self.html

        with open(path, 'w') as f:
            f.write(html)

    def _set_html(self) -> None:
        self._body = ''

        for line in self._parser.parse['document']:
            tag_start = '<' + self._map[line.type]
            if line.classes:
                tag_start += f' class="{' '.join(line.classes)}"'

            if line.properties:
                for key, value in line.properties.items():
                    tag_start += f' {key}="{value}"'
            
            if line.styles:
                tag_start += ' style="'
                for key, value in line.styles.items():
                    tag_start += f'{key}: {value}; '
                tag_start += '"'

            tag_start += '>'

            content = ''
            # for run in line.runs:
            #     print('    ', run)

            tag_end = f'</{self._map[line.type]}>\n'

            tag = tag_start + content + tag_end
            self._body += tag.replace(' "', '"')

        for line in self._parser.parse['comments']:
            tag_start = MODAL_START

            content = ''
            # for run in line.runs:
            #     print('    ', run)

            if line.type == 'Comment': tag_end = MODAL_END

            tag = tag_start + content + tag_end
            self._body += tag.replace(' "', '"')

    @staticmethod
    def _get_map():
        tags_map = {f'Heading {x}': f'h{x}' for x in range(1, 10)}
        tags_map.update({
            'Quote': 'blockquote', 'Paragraph': 'p', 'Title': 'h1',
            'Comment': 'div',
            })
        return tags_map

if __name__ == '__main__':
    html = DocxHTML('~/doc.docx')
    html.html
    html.save()
