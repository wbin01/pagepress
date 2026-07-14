#!/usr/bin/env python3
import base64
import re

from zipfile import ZipFile


class Run(object):
    """..."""
    def __init__(self, xml: str, parent: DocxParse) -> None:
        """..."""
        self._xml = xml
        self._parent = parent

        self._xml_styles = self._parent._parent._xml_styles
        self._xml_rels = self._parent._parent._xml_rels
        self._path = self._parent._parent._path

        self._img_as_base64 = False
        self._xml_shape = ''
        self._meta = {}

        self._type = self._set_type()
        self._text = self._set_text()
        self._properties = self._set_properties()
        self._tags = self._set_tags()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(xml)'

    @property
    def properties(self) -> dict:
        """..."""
        return self._properties

    @property
    def tags(self) -> list:
        """..."""
        return self._tags

    @property
    def text(self) -> str:
        """..."""
        return self._text

    @property
    def type(self) -> str:
        """..."""
        return self._type
        
    def _set_type(self) -> str:
        if '<mc:AlternateContent>' in self._xml:
            shape = re.findall(r'<v:shape .+</v:shape>', self._xml, re.DOTALL)
            if shape:
                self._xml_shape = shape[0]

                if '<v:imagedata' in shape[0]:
                    return 'Image'

                elif '<v:path ' in shape[0] and '<v:stroke ' in shape[0]:
                    return 'Draw'
        return 'Text'

    def _set_text(self) -> str:
        if self._type == 'Text':
            if '<w:t ' in self._xml:
                tx = re.findall(r'<w:t [^>]+>(.*)</w:t>', self._xml, re.DOTALL)
                if tx: return tx[0]
        return ''

    def _set_properties(self) -> dict:
        properties = {}
        if self._type == 'Image':
            id_ = src = ext = width = height = ''

            data = re.findall(r'<v:imagedata[^>]+>', self._xml, re.DOTALL)
            if data: id_ = re.findall(r'r:id="(rId\d+)"', data[0])

            if id_:
                for rel in self._xml_rels:
                    if rel.get('Id') == id_[0]:
                        src = 'word/' + rel.get('Target')
                        ext = src.split('.')[-1].lower()
                        break

            if src and self._parent._parent._img_base64:
                with ZipFile(self._path) as f:
                    src = base64.b64encode(f.read(src)).decode('ascii')
                    src = f'data:image/{ext};base64,{src}'

            if self._xml_shape:
                w = re.findall(r'width:(\d+)', self._xml_shape)
                if w: width = int(int(w[0]) * (96 / 72))
                h = re.findall(r'height:(\d+)', self._xml_shape)
                if h: height = int(int(h[0]) * (96 / 72))

            properties['src'] = src
            properties['width'] = width
            properties['height'] = height
            self._meta['extension'] = ext

        elif self._type == 'Draw':
            pass

        return properties

    def _set_tags(self) -> list:
        tags = []
        # link
        link = re.findall(f'<w:hyperlink [^>]+>', self._xml, re.DOTALL)
        if link:
            id_ = re.findall(r'r:id=\"([^\"]+)\"', link[0], re.DOTALL)
            id_ = id_[0] if id_ else ''

            href = re.findall(r'w:tooltip=\"([^\"]+)\"', link[0], re.DOTALL)
            href = href[0] if href else ''

            tags.append({'tag': 'a', 'href': href})

        if self._type == 'Image':
            href = target = ''
            if '<a:hlinkClick r:id=' in self._xml:
                id_ = re.findall(
                    f'<a:hlinkClick r:id=\"([^\"]*)\" tooltip=\"[^\"]*\"/>',
                    self._xml, re.DOTALL)
                if id_:
                    for rel in self._xml_rels:
                        if rel.get('Id') == id_[0]:
                            href = rel.get('Target')
                            target = rel.get('TargetMode')
            if href:
                if target == 'External': target = '_blank'
                tags.append({'tag': 'a', 'href': href, 'target': target})

        # Highlight
        if '<w:highlight w:val="' in self._xml:
            highlight = re.findall(
                f'<w:highlight w:val=\"([^\"]*)\"', self._xml, re.DOTALL)

            if highlight[0] != 'none':
                tags.append({
                    'tag': 'span',
                    'class': f'highlight-{highlight[0]}',
                    'style': f'background-color: {highlight[0]};'})

        # Comment
        if '<w:commentRangeStart ' in self._xml:
            id_ = re.findall(
                r'<w:commentRangeStart w:id=\"([^\"]*)\"', self._xml)
            id_ = id_[0] if id_ else ''
            tags.append({
                'tag': 'a', 'type': 'button', 'class': f'comment-button',
                'data-bs-toggle': 'modal', 'data-bs-target': f'#modal{id_}',
                'id': id_,})

        if '<w:b/>' in self._xml:
            tags.append({'tag': 'b'})

        if '<w:strike/>' in self._xml:
            tags.append({'tag': 's'})

        if '<w:u w:val="single"/>' in self._xml:
            tags.append({'tag': 'u'})

        if '<w:i/>' in self._xml:
            tags.append({'tag': 'i'})

        return tags
