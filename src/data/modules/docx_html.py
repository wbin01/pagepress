#!/usr/bin/env python3
import base64
import os
import re

from lxml import etree
from pathlib import Path
from zipfile import ZipFile


class Line(object):
    def __init__(self, xml: str) -> None:
        self._xml = xml

        self._childrens = []
        self._properties = {}
        self._classes = {}
        self._styles = {}

        self._set_childrens()
        self._set_properties()

    def _set_childrens(self) -> dict:
        xml = self._xml.lstrip('<w:p>').rstrip('</w:p>').strip()

        properties = re.findall(r'<w:pPr>.*</w:pPr>', xml, re.DOTALL)
        self._xml = properties[0] if properties else ''

        childrens = xml.replace(self._xml, '').split('</w:r>')
        for child in childrens:
            self._childrens.append(Child(child))

    def _set_properties(self) -> None:
        if '<w:jc w:val=' in self._xml:
            align = re.findall(r'<w:jc w:val=\"([^\"]*)\"',self._xml,re.DOTALL)
            if align: self._styles['align'] = align[0]

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(xml)'


class Child(object):
    def __init__(self, xml: str) -> None:
        self._xml = xml

        self._child_type = 'text'
        self._text = ''
        self._source = ''
        self._classes = {}
        self._properties = {}
        self._tags = []

        self._set_child_type()
        self._set_content()
        self._set_tags()

    def _set_child_type(self) -> None:
        if '<v:imagedata' in self._xml:
            self._child_type = 'image'

    def _set_content(self) -> None:
        if self._child_type == 'text':
            if '<w:t ' in self._xml:
                txt = re.findall(r'<w:t [^>]+>(.*)</w:t>',self._xml, re.DOTALL)
                if txt: self._text = txt[0]

    def _set_tags(self) -> None:
        link = re.findall(f'<w:hyperlink [^>]+>', self._xml, re.DOTALL)
        if link:
            id_ = re.findall(r'r:id=\"([^\"]+)\"', link[0], re.DOTALL)
            id_ = id_[0] if id_ else ''

            src = re.findall(r'w:tooltip=\"([^\"]+)\"', link[0], re.DOTALL)
            src = src[0] if src else ''

            self._tags.append({'tag': 'a', 'id': id_, 'src': src})

        if '<w:b/>' in self._xml:
            self._tags.append({'tag': 'b'})


class DocxHTML(object):
    def __init__(self, path: str) -> None:
        self._path = Path(os.path.expanduser(path)).as_posix()

        with ZipFile(self._path) as f:  # f.read(url).decode('utf-8')
            self._xml_comments = etree.parse(f.open('word/comments.xml'))
            self._xml_document = etree.parse(f.open('word/document.xml'))
            self._xml_rels = etree.parse(f.open('word/_rels/document.xml.rels'))
            self._xml_styles = etree.parse(f.open('word/styles.xml'))

        self._name_space_doc = {'w':
            'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        self._name_space_rel = {'r':
            'http://schemas.openxmlformats.org/package/2006/relationships'}

        self._parse_comments = self._get_parse_comments()
        self._parse_document = self._get_parse_document()
        self._parse_rels = self._get_parse_rels()
        self._parse_styles = self._get_parse_styles()

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

            lines.append(Line(line))

        return lines

    def _get_parse_rels(self) -> list:
        if not self._xml_rels: return []

        parse = []
        for xml in self._xml_rels.xpath(
                '//r:Relationship', namespaces=self._name_space_rel):
            # # Imgage ID
            # if xml.get('Id') == parse['meta']['id']:
            #     parse['meta']['url'] = xml.get('Target')
            pass

        return parse

    def _get_parse_styles(self) -> list:
        if not self._xml_styles: return []

        parse = []
        for xml in self._xml_styles.xpath(
                '//w:style', namespaces=self._name_space_doc):
            xml = etree.tostring(xml, encoding='unicode',pretty_print=True)
            xml_style = re.sub(
                r'<w:style.+w:styleId=\"', '<w:style w:styleId="', xml,count=1)
            pass

        return parse


if __name__ == '__main__':
    from pprint import pprint

    parser = DocxHTML('~/doc.docx')
    print(parser)
    for line in parser._parse_document:
        # pprint(line._xml)
        # pprint(line._properties)

        for c in line._childrens:
            print('type:')
            pprint(c._child_type)

            print('text/source:')
            pprint(c._text) if c._child_type == 'text' else pprint(c._source)
            
            print('properties:')
            pprint(c._properties)
            
            print('tags:')
            pprint(c._tags)

            print('xml:')
            pprint(c._xml)

            print('---')
