#!/usr/bin/env python3
import base64
import os
import re

from lxml import etree
from pathlib import Path
from zipfile import ZipFile


class DocxParse(object):
    def __init__(self, path: str) -> None:
        self._path = Path(os.path.expanduser(path)).as_posix()

        with ZipFile(self._path) as f:  # f.read(url).decode('utf-8')
            self._xml_comments = etree.parse(f.open('word/comments.xml'))
            self._xml_document = etree.parse(f.open('word/document.xml'))
            self._xml_rels = etree.parse(f.open('word/_rels/document.xml.rels'))
            self._xml_styles = etree.parse(f.open('word/styles.xml'))

        self._name_space_doc = {'w':
            'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

        self._name_space_rels = {'r':
            'http://schemas.openxmlformats.org/package/2006/relationships'}
        
        self._rels = self._xml_rels.xpath(
                '//r:Relationship', namespaces=self._name_space_rels)

        self._styles = [
            re.sub(r'<w:style.+w:styleId=\"', '<w:style w:styleId="',
                etree.tostring(xml, encoding='unicode', pretty_print=True),
                count=1)
            for xml in self._xml_styles.xpath(
                '//w:style', namespaces=self._name_space_doc)]

        self._parse_comments = self._get_parse_comments()
        self._parse_document = self._get_parse_document()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self._path}")'

    def _get_parse_comments(self) -> list:
        if not self._xml_comments: return []

        comments = etree.tostring(
            self._xml_comments, encoding='unicode', pretty_print=True)
        if not comments: return []

        parse = []
        for xml in comments.split('</w:comments>')[0].split('</w:comment>'):
            xml = re.sub(r'<w:comments [^>]+>', '<w:comments>', xml)
            pass

        return parse

    def _get_parse_document(self) -> list:
        if not self._xml_document: return []

        lines = []
        for xml in self._xml_document.xpath(
                '//w:body/w:p', namespaces=self._name_space_doc):
            xml = etree.tostring(xml, encoding='unicode', pretty_print=True)
            line = re.sub(r'<w:p\b[^>]*>', '<w:p>', xml, count=1)

            lines.append(Line(line, self))

        return lines


class Line(object):
    def __init__(self, xml: str, parent: DocxParse) -> None:
        self._xml = xml
        self._parent = parent

        self._xml_styles = self._parent._styles
        self._xml_rels = self._parent._rels
        self._path = self._parent._path

        self._type = 'Paragraph'
        self._properties = {}
        self._styles = {}
        self._runs = []

        self._set_type()
        self._set_runs()
        self._set_properties()

    def _set_type(self) -> None:
        if '<w:pStyle w:val="' in self._xml:
            id_ = re.findall(
                r'<w:pStyle w:val=\"(\d+)\"/>', self._xml, re.DOTALL)
            if not id_: return
            
            for style in self._xml_styles:
                if re.findall(fr'<w:style w:styleId=\"{id_[0]}\">', style):
                    type_ = re.findall(r'<w:name w:val=\"([^\"]+)\"/>', style)
                    if type_: self._type = type_[0]

    def _set_runs(self) -> None:
        xml = self._xml.lstrip('<w:p>').rstrip('</w:p>').strip()

        properties = re.findall(r'<w:pPr>.*</w:pPr>', xml, re.DOTALL)
        self._xml = properties[0] if properties else ''

        runs = xml.replace(self._xml, '').split('</w:r>')
        for run in runs:
            run = Run(run, self._parent)
            if self._run_is_valid(run): self._runs.append(run)

    def _set_properties(self) -> None:
        if '<w:jc w:val=' in self._xml:
            align = re.findall(r'<w:jc w:val=\"([^\"]*)\"',self._xml,re.DOTALL)
            if align: self._styles['align'] = align[0]

    def _run_is_valid(self, run) -> bool:
        conditions = [
            run._type == 'Text',
            not run._text,
            not run._properties,
            not run._tags,
            not run._meta]

        if all(conditions):
            return False
        return True


    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(xml)'


class Run(object):
    def __init__(self, xml: str, parent: DocxParse) -> None:
        self._xml = xml
        self._parent = parent

        self._xml_styles = self._parent._styles
        self._xml_rels = self._parent._rels
        self._path = self._parent._path

        self._img_as_base64 = False
        self._xml_shape = ''

        self._type = 'Text'
        self._text = ''
        self._properties = {}
        self._tags = []
        self._meta = {}

        self._set_type()
        self._set_text()
        self._set_properties()
        self._set_tags()

    def _set_type(self) -> None:
        if '<mc:AlternateContent>' in self._xml:
            shape = re.findall(r'<v:shape .+</v:shape>', self._xml, re.DOTALL)
            if shape:
                self._xml_shape = shape[0]

                if '<v:imagedata' in shape[0]:
                    self._type = 'Image'

                elif '<v:path ' in shape[0] and '<v:stroke ' in shape[0]:
                    self._type = 'Draw'

    def _set_text(self) -> None:
        if self._type == 'Text':
            if '<w:t ' in self._xml:
                txt = re.findall(r'<w:t [^>]+>(.*)</w:t>',self._xml, re.DOTALL)
                if txt: self._text = txt[0]

    def _set_properties(self) -> None:
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

            if src and self._img_as_base64:
                with ZipFile(self._path) as f:
                    src = base64.b64encode(f.read(src)).decode('ascii')
                    src = f'data:image/{ext};base64,{src}'

            if self._xml_shape:
                w = re.findall(r'width:(\d+)', self._xml_shape)
                if w: width = int(int(w[0]) * (96 / 72))
                h = re.findall(r'height:(\d+)', self._xml_shape)
                if h: height = int(int(h[0]) * (96 / 72))

            self._properties['src'] = src
            self._properties['width'] = width
            self._properties['height'] = height
            self._meta['extension'] = ext

        elif self._type == 'Draw':
            pass

    def _set_tags(self) -> None:
        link = re.findall(f'<w:hyperlink [^>]+>', self._xml, re.DOTALL)
        if link:
            id_ = re.findall(r'r:id=\"([^\"]+)\"', link[0], re.DOTALL)
            id_ = id_[0] if id_ else ''

            href = re.findall(r'w:tooltip=\"([^\"]+)\"', link[0], re.DOTALL)
            href = href[0] if href else ''

            self._tags.append({'tag': 'a', 'href': href})

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
                self._tags.append({'tag': 'a', 'href': href, 'target': target})


        if '<w:highlight w:val="' in self._xml:
            highlight = re.findall(
                f'<w:highlight w:val=\"([^\"]*)\"', self._xml, re.DOTALL)

            if highlight[0] != 'none':
                self._tags.append({
                    'tag': 'span',
                    'class': f'highlight-{highlight[0]}',
                    'style': f'background-color: {highlight[0]};'})

        if '<w:b/>' in self._xml:
            self._tags.append({'tag': 'b'})

        if '<w:strike/>' in self._xml:
            self._tags.append({'tag': 's'})

        if '<w:u w:val="single"/>' in self._xml:
            self._tags.append({'tag': 'u'})

        if '<w:i/>' in self._xml:
            self._tags.append({'tag': 'i'})

if __name__ == '__main__':
    from pprint import pprint

    parser = DocxParse('~/doc.docx')
    # print(parser)
    for line in parser._parse_document:
        # print('type: ', end='')
        # pprint(line._type)
        # print('properties: ', end='')
        # pprint(line._properties)
        # print('xml: ', end='')
        # pprint(line._xml)
        for c in line._runs:
            # if c._type == 'Image':
            print('---')
            print('type: ', end='')
            pprint(c._type)
            print('text: ', end='')
            pprint(c._text)
            print('properties: ', end='')
            pprint(c._properties)
            print('tags: ', end='')
            pprint(c._tags)
            print('meta: ', end='')
            pprint(c._meta)
            # print('xml: ', end='')
            # pprint(c._xml)
        print('===')
