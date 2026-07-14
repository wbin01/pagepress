#!/usr/bin/env python3
import re

from .docx_parse_run import Run


class Line(object):
    """..."""
    def __init__(self, xml: str, parent: DocxParse) -> None:
        """..."""
        self._xml = xml
        self._parent = parent

        self._xml_styles = self._parent._xml_styles
        self._xml_rels = self._parent._xml_rels
        self._path = self._parent._path

        self._properties = {}
        self._type = self._set_type()
        self._runs = self._set_runs()
        self._classes = self._set_classes()
        self._styles = self._set_styles()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(xml)'

    @property
    def classes(self) -> list:
        """..."""
        return self._classes

    @property
    def properties(self) -> dict:
        """..."""
        return self._properties

    @property
    def runs(self) -> list:
        """..."""
        return self._runs

    @property
    def styles(self) -> dict:
        """..."""
        return self._styles

    @property
    def type(self) -> str:
        """..."""
        return self._type

    def _set_classes(self) -> list:
        classes = []
        if self._type == 'Title':
            classes.append('post-tittle')

        elif self._type == 'Comment':
            classes.append('comment-modal')

        return classes

    def _set_runs(self) -> list:
        runs = []
        if self._type == 'Comment':
            id_ = re.findall(r'<w:comment w:id="([^"]+)"', self._xml)
            if id_:
                self._properties['id'] = id_[0]

                for xml in self._xml.split('</w:r>'):
                    run = Run(xml, self)
                    
                    if run._type == 'Text' and not run._text:
                        continue
                    runs.append(run)
        else:
            xml = self._xml.lstrip('<w:p>').rstrip('</w:p>').strip()
            properties = re.findall(r'<w:pPr>.*</w:pPr>', xml, re.DOTALL)
            self._xml = properties[0] if properties else ''

            for xml in xml.replace(self._xml, '').split('</w:r>'):
                run = Run(xml, self)

                if run._type == 'Text' and not run._text:
                    continue
                runs.append(run)

        return runs

    def _set_styles(self) -> dict:
        styles = {}
        if '<w:jc w:val=' in self._xml:
            align = re.findall(r'<w:jc w:val=\"([^\"]*)\"',self._xml,re.DOTALL)
            if align: styles['text-align'] = align[0]
        return styles

    def _set_type(self) -> str:
        if '<w:pStyle w:val="' in self._xml:
            id_ = re.findall(
                r'<w:pStyle w:val=\"(\d+)\"/>', self._xml, re.DOTALL)
            if not id_: return
            
            for style in self._xml_styles:
                if re.findall(fr'<w:style w:styleId=\"{id_[0]}\">', style):
                    type_ = re.findall(r'<w:name w:val=\"([^\"]+)\"/>', style)
                    if type_: return type_[0]

        elif '<w:comment w:id=' in self._xml:
            return 'Comment'

        return 'Paragraph'
