#!/usr/bin/env python3
import re
import base64
from zipfile import ZipFile
from lxml import etree


class DocxParser(object):
    def __init__(self, path: str) -> None:
        self._path = path

        # Files
        with ZipFile(path) as docx:  # docx.read(url).decode('utf-8')
            self._doc = etree.parse(docx.open('word/document.xml'))
            self._styles = etree.parse(docx.open('word/styles.xml'))
            self._rel = etree.parse(docx.open('word/_rels/document.xml.rels'))
            # self._comments = etree.parse(docx.open('word/comments.xml'))

        # Name space parsers
        self._doc_ns = {'w':
            'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        self._rel_ns = {'r':
            'http://schemas.openxmlformats.org/package/2006/relationships'}

        # Parsers
        self._styles_parse = self._set_style_parse()
        self._doc_parse = self._set_doc_parse()
        self._comments_parse = self._set_comments_parse()
        # self._rel_parse = []

        self._parse = {
            'body': self._doc_parse, 'comments': self._comments_parse}

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self._path}")'

    @property
    def parse(self) -> str:
        return self._parse

    @property
    def path(self) -> str:
        return self._path

    def print(
            self,
            hidde_xml: bool = True,
            hidde_xml_style: bool = True) -> None:
        print('=== BODY ===')
        print()
        self._parse_print(self._doc_parse, hidde_xml, hidde_xml_style)
        print()
        print('=== COMMENTS ===')
        print()
        self._parse_print(self._comments_parse, hidde_xml, hidde_xml_style)

    def _parse_print(
            self,
            parse_list: list,
            hidde_xml: bool = True,
            hidde_xml_style: bool = True) -> None:

        for x in parse_list:
            for k, v in x.items():
                if k == 'children':
                    if not v:
                        print(f"'children': {v},")
                    else:
                        print(f"'children': [")
                        for c in v:
                            if 'text' in c and c['tags']:
                                print(
                                    f"  {{'text': '{c["text"]}', 'tags': [",
                                    end='')
                                for n, t in enumerate(c['tags']):
                                    comma = ',' if n != 0 else ''
                                    print(f'{comma}\n    {t}', end='')
                                print(']},')
                            else:
                                print(f'  {c},')
                        print('  ],')

                elif k == 'pr' or k == 'meta' or k == 'style':
                    if not v:
                        print(f"'{k}': {v},")
                        continue

                    print(f"'{k}': {{")
                    for i, j in v.items():
                        if i == 'src':
                            print(f"  '{i}': '{j[:44]}...',")
                        elif i == 'xml_style':
                            if not j:
                                print(f"  '{i}': '',")
                            elif hidde_xml_style:
                                print(f"  '{i}': " f"'{j.replace('\n', ''
                                    ).replace(' ', '')[:38] + "...'"},")
                            else:
                                print(f"  '{i}': '''\n{j}''',")
                        
                        elif i == 'xml_doc':
                            if hidde_xml:
                                print(f"  'xml_doc': '{j.replace('\n', ''
                                    ).replace(' ', '')[:40] + "...'"},")
                            else:
                                print(f"  'xml_doc': '''\n{j}'''")
                        else:
                            print(f"  '{i}': " f"'{j}',")

                    print(  '},')
                else:
                    print(f"'{k}': '{v}',")

            if x != parse_list[-1]: print('---')

    def _set_comments_parse(self) -> list:
        comments_parse = []
        # Comments modal
        with ZipFile(self._path) as docx:  # docx.namelist()
            comments = etree.parse(docx.open('word/comments.xml'))

        comments = etree.tostring(
            comments, encoding='unicode', pretty_print=True)
        if not comments: return

        for xml in comments.split('</w:comments>')[0].split('</w:comment>'):
            xml = re.sub(r'<w:comments [^>]+>', '<w:comments>', xml)

            parse = {'tag': '', 'children': [], 'pr': {}, 'style':{}, 'meta': {
                'id': '', 'xml_doc': xml, 'xml_style': '', 'source': 'docx'}}
            parse['tag'] = 'comment_modal'

            id_ = re.findall(r'<w:comment w:id="([^"]+)"', xml)
            if not id_: continue
            parse['meta']['id'] = id_[0]

            for run in xml.split('</w:r>'):
                txt = re.findall(r'<w:t xml:space="preserve">(.+)<\/w:t>', run)
                if not txt: continue

                tag = {'tag': 'p', 'pr': {}}
                parse['children'].append({'text': txt[0], 'tags': [tag]})

            if parse['meta']['id']: comments_parse.append(parse)
        return comments_parse

    def _set_doc_parse(self) -> list:
        doc_parse = []
        tag_converter = {f'Heading {x}': f'h{x}' for x in range(1, 10)}
        tag_converter['Quote'] = 'blockquote'

        for xml in self._doc.xpath('//w:body/w:p', namespaces=self._doc_ns):
            xml = etree.tostring(xml, encoding='unicode', pretty_print=True)
            xml = re.sub(r'<w:p\b[^>]*>', '<w:p>', xml, count=1)
            
            parse = {'tag': '', 'children': [], 'pr': {}, 'style':{}, 'meta': {
                'id': '', 'xml_doc': xml, 'xml_style': '', 'source': 'docx'}}

            # H, Quote...
            if '<w:pStyle w:val="' in xml:
                # id
                id_ = re.findall(r'<w:pStyle w:val=\"(\d+)\"/>', xml)
                if id_: parse['meta']['id'] = id_[0]

                # pr: style
                for style in self._styles_parse:
                    s = re.findall(fr'<w:style w:styleId=\"{id_[0]}\">', style)
                    if s:
                        parse['meta']['xml_style'] = style
                        break

                if not parse['meta']['id']: continue

                # tag
                tag = re.findall(
                    r'<w:name w:val=\"([^\"]+)\"/>',parse['meta']['xml_style'])
                if tag:
                    tag = tag[0]
                    if tag in tag_converter: tag = tag_converter[tag]
                    parse['tag'] = tag

            # Image
            elif '<v:imagedata' in xml:
                # id, tag
                data = re.findall(r'<v:imagedata[^>]+>', xml)
                if data:
                    id_ = re.findall(r'r:id="(rId\d+)"', data[0])
                    if id_: parse['meta']['id'], parse['tag'] = id_[0], 'img'

                if not parse['meta']['id']: continue

                # pr: url
                for rel in self._rel.xpath(
                        '//r:Relationship', namespaces=self._rel_ns):
                    if rel.get('Id') == parse['meta']['id']:
                        parse['meta']['url'] = rel.get('Target')
                        break

                # pr: src
                with ZipFile(self._path) as docx:
                    data = docx.read('word/' + parse['meta']['url'])
                pr_source = (
                    'data:image/ext;base64,' + base64.b64encode(
                        data).decode('ascii'))

                # pr
                shape = re.findall(r'<v:shape [^>]+>', xml)
                if shape:
                    # width, height
                    w = re.findall(r'width:(\d+)', shape[0])
                    if w: parse['pr']['width'] = int(int(w[0]) * (96 / 72))
                    h = re.findall(r'height:(\d+)', shape[0])
                    if h: parse['pr']['height'] = int(int(h[0]) * (96 / 72))

                    # extension
                    parse['meta']['ext'] = parse[
                        'meta']['url'].split('.')[-1].lower()

                    parse['pr']['src'] = pr_source.replace(
                        'data:image/ext;base64,',
                        f'data:image/{parse['meta']['ext']};base64,')

                parse['style']['max-width'] = '100%'
            # P
            else:
                # id, tag
                parse['meta']['id'] = parse['tag'] = 'p'

            # Runs children tags
            tag_converter.update({
                '<w:b/>': 'b', '<w:i/>': 'i', '<w:strike/>': 's',
                '<w:u w:val="single"/>': 'u', '<w:highlight w:val="': 'bg',
                '<w:hyperlink ': 'a', '<w:commentRangeStart ': 'comment'})

            # children
            for run in xml.split('</w:r>'):
                txt = re.findall(r'<w:t [^>]+>([^<]+)</w:t>', run)
                
                tags = []
                for k, v in tag_converter.items():
                    tag = {'tag': '', 'pr': {}}
                    if k in run:
                        if k == '<w:highlight w:val="':
                            if '<w:highlight w:val="none"/>' not in run:
                                tag['tag'] = v
                                tags.append(tag)

                        elif k == '<w:hyperlink ':
                            link = re.findall('<w:hyperlink '
                                r'.+w:tooltip=\"([^\"]+)\"[^>]+>', run)
                            if link:
                                tag['tag'] = v
                                tag['pr']['href'] = link[0]
                                tags.append(tag)

                        elif k == '<w:commentRangeStart ':
                            comt = re.findall('<w:commentRangeStart w:id'
                                r'=\"([^\"]+)\"/>', run)
                            if comt:
                                tag['tag'] = v
                                tag['pr']['id'] = comt[0]
                                tags.append(tag)
                        else:
                            tag['tag'] = v
                            tags.append(tag)
                if txt:
                    children = {'text': txt[0], 'tags': tags}
                    # Before: <u><i> te</i></u> <u><i>xt </i></u>
                    # Now:    <u><i> text </i></u>
                    if parse['children']:
                        last = parse['children'][-1]
                        lt = [x['tag'] for x in last['tags']]
                        ct = [x['tag'] for x in children['tags']]
                        if lt == ct:
                            parse['children'][-1]['text'] += children['text']
                        else:
                            for t in txt: parse['children'].append(children)
                    else:
                        for t in txt: parse['children'].append(children)

            # pr: align
            align = re.findall(r'<w:jc w:val=\"([^\"]+)\"/>', xml)
            if align: parse['style']['align'] = align[0]

            if parse['meta']['id']:
                if parse['tag'] != 'img' and not parse['children']:
                    continue
                doc_parse.append(parse)

        return doc_parse

    def _set_style_parse(self) -> list:
        styles_parse = []
        style, find, ns = '', r'<w:style.+w:styleId=\"', self._doc_ns
        for x in self._styles.xpath('//w:style', namespaces=ns):
            x = etree.tostring(x, encoding='unicode',pretty_print=True)
            style = re.sub(find, '<w:style w:styleId="', x, count=1)
            styles_parse.append(style)
        return styles_parse


if __name__ == '__main__':
    parser = DocxParser('/home/user/Dev/github/pagepress/src/docs/en-US/Religion/Em Nome do Pai.docx')
    # print(parser)
    parser.print(True, True)
