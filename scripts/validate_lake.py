#!/usr/bin/env python3
"""Check the local lake authoring profile. Does not verify Yuque import."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re


class LakeParser(HTMLParser):
    VOID_TAGS = {'meta', 'col', 'br', 'img', 'hr', 'link', 'input'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {'tag': 'root', 'attrs': {}, 'children': [], 'text': ''}
        self.stack = [self.root]
        self.nodes = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'children': [], 'text': ''}
        self.stack[-1]['children'].append(node)
        self.nodes.append(node)
        if tag not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1]['tag'] != tag:
            self.errors.append(f'Unexpected closing tag: {tag}')
            return
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1]['text'] += data


def descendants(node, tag):
    result = []
    for child in node['children']:
        if child['tag'] == tag:
            result.append(child)
        result.extend(descendants(child, tag))
    return result


def validate(source):
    parser = LakeParser()
    parser.feed(source)
    parser.close()
    errors = parser.errors
    if not source.lstrip('\ufeff').lower().startswith('<!doctype lake>'):
        errors.append('Document must begin with <!doctype lake>.')
    if len(parser.stack) != 1:
        errors.append('Unclosed tags remain.')
    titles = descendants(parser.root, 'title')
    if len(titles) != 1 or not titles[0]['text'].strip():
        errors.append('Exactly one non-empty title is required.')
    required_meta = {'doc-version': '1', 'viewport': 'adapt',
                     'typography': 'classic', 'paragraphSpacing': 'relax'}
    for name, value in required_meta.items():
        matches = [node for node in parser.nodes
                   if node['tag'] == 'meta' and node['attrs'].get('name') == name]
        if len(matches) != 1 or matches[0]['attrs'].get('content') != value:
            errors.append(f'Missing or invalid meta: {name}')
    ids = set()
    for node in parser.nodes:
        tag, attrs = node['tag'], node['attrs']
        if tag in {'html', 'head', 'body', 'script', 'button'}:
            errors.append(f'Unexpected document or copy-page element: {tag}')
        if tag in {'h1', 'h2', 'h3', 'table'}:
            identifier = attrs.get('id', '')
            if not re.fullmatch(r'[A-Za-z0-9]{6,8}', identifier):
                errors.append(f'Invalid ID on {tag}: {identifier}')
            if attrs.get('data-lake-id') != identifier:
                errors.append(f'Mismatched data-lake-id on {tag}.')
            if identifier in ids:
                errors.append(f'Duplicate ID: {identifier}')
            ids.add(identifier)
        elif 'id' in attrs or 'data-lake-id' in attrs:
            errors.append(f'Unexpected ID on {tag}.')
        if tag == 'ol':
            if not attrs.get('list'):
                errors.append('Ordered list is missing its list identifier.')
            for attribute, minimum in [('start', 1), ('data-lake-indent', 0)]:
                value = attrs.get(attribute, str(minimum))
                if not re.fullmatch(r'[0-9]+', value or '') or int(value) < minimum:
                    errors.append(f'Invalid list attribute: {attribute}')
            if not node['children'] or any(child['tag'] != 'li' for child in node['children']):
                errors.append('Ordered lists must contain li children.')
    for table in descendants(parser.root, 'table'):
        columns = descendants(table, 'col')
        rows = descendants(table, 'tr')
        if not columns or not rows:
            errors.append('Table needs columns and rows.')
        for row in rows:
            cells = [child for child in row['children'] if child['tag'] == 'td']
            if len(cells) != len(columns):
                errors.append('Table row cell count differs from column count.')
            if any('colspan' in cell['attrs'] or 'rowspan' in cell['attrs'] for cell in cells):
                errors.append('Merged cells require separate validation.')
    if re.search(r'</ol>\s+<ol\b', source, re.I):
        errors.append('Adjacent list blocks must have no whitespace between them.')
    return errors


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('input', type=Path)
    args = cli.parse_args()
    try:
        errors = validate(args.input.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError) as error:
        cli.exit(2, f'{error}\n')
    if errors:
        cli.exit(1, '\n'.join(errors) + '\n')
    print('Local lake structure checks passed. Content and Yuque import require separate verification.')


if __name__ == '__main__':
    main()
