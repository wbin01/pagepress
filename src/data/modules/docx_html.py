#!/usr/bin/env python3
import base64
import os
import re

from lxml import etree
from pathlib import Path
from zipfile import ZipFile


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

        parse = []
        for xml in self._xml_document.xpath(
                '//w:body/w:p', namespaces=self._name_space_doc):
            xml = etree.tostring(xml, encoding='unicode', pretty_print=True)
            xml = re.sub(r'<w:p\b[^>]*>', '<w:p>', xml, count=1)
            pass

        return parse

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
