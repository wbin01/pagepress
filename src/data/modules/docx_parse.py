#!/usr/bin/env python3
import os
import re

from lxml import etree
from pathlib import Path
from zipfile import ZipFile

from .docx_parse_line import Line


NS_DOC = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
NS_REL = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}


class DocxParse(object):
    """..."""
    def __init__(self, path: str, img_base64: bool = False) -> None:
        """..."""
        self._path = Path(os.path.expanduser(path)).as_posix()

        self._img_base64 = img_base64
        self._xml_rels = self._get_rels()
        self._xml_styles = self._get_styles()
        self._comments = self._get_comments()
        self._document = self._get_document()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self._path}")'

    @property
    def path(self) -> str:
        """..."""
        return self._path

    @property
    def parse(self) -> dict:
        """..."""
        return {'document': self._document, 'comments': self._comments}

    def _get_comments(self) -> list:
        try:
            with ZipFile(self._path) as f:  # docx.namelist()
                comments = etree.parse(f.open('word/comments.xml'))
        except:
            return []

        if not comments: return []

        comments = etree.tostring(
            comments, encoding='unicode', pretty_print=True)
        if not comments: return parse

        lines = []
        for xml in comments.split('</w:comment>'):
            line = re.sub(r'<w:comments [^>]+>', '<w:comments>', xml)
            lines.append(Line(line, self))

        return lines

    def _get_document(self) -> list:
        try:
            with ZipFile(self._path) as f:  # docx.namelist()
                document = etree.parse(f.open('word/document.xml'))
        except:
            return parse

        if not document: return []

        lines = []
        for xml in document.xpath(
                '//w:body/w:p', namespaces=NS_DOC):
            xml = etree.tostring(xml, encoding='unicode', pretty_print=True)
            line = re.sub(r'<w:p\b[^>]*>', '<w:p>', xml, count=1)
            lines.append(Line(line, self))

        return lines

    def _get_rels(self):
        try:
            with ZipFile(self._path) as f:  # f.read(url).decode('utf-8')
                xml_rels = etree.parse(f.open('word/_rels/document.xml.rels'))
        except:
            return []
        
        return xml_rels.xpath('//r:Relationship', namespaces=NS_REL)

    def _get_styles(self):
        parse = []
        try:
            with ZipFile(self._path) as f:  # f.read(url).decode('utf-8')
                xml_styles = etree.parse(f.open('word/styles.xml'))
        except:
            return parse

        for xml in xml_styles.xpath('//w:style', namespaces=NS_DOC):
            s = etree.tostring(xml, encoding='unicode', pretty_print=True)
            parse.append(re.sub(
                r'<w:style.+w:styleId=\"', '<w:style w:styleId="', s, count=1))
        return parse


if __name__ == '__main__':
    from pprint import pprint

    parser = DocxParse('~/doc.docx')
    # print(parser)
    for line in parser._document:
        print('type: ', end='')
        pprint(line._type)
        print('properties: ', end='')
        pprint(line._properties)
        print('styles: ', end='')
        pprint(line._styles)
        # print('xml: ', end='')
        # pprint(line._xml)
        for c in line._runs:
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
