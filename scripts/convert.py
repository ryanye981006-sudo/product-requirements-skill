#!/usr/bin/env python3
"""Convert PRD-style Markdown tables to a self-contained Yuque row-copy HTML."""

import argparse
from html import escape
from pathlib import Path
import re


class ConversionError(ValueError):
    """Input cannot be converted without losing its table structure."""


def split_row(line):
    """Split pipe-table cells while preserving escaped literal pipes."""
    text = line.strip()
    if not text.startswith('|') or not text.endswith('|'):
        raise ConversionError('Table rows must start and end with |.')
    result, current = [], []
    for character in text[1:-1]:
        if character == '|' and not (len(current) - len(''.join(current).rstrip('\\'))) % 2:
            result.append(''.join(current).strip())
            current = []
        else:
            current.append(character)
    result.append(''.join(current).strip())
    return result


def inline(text):
    # Escape raw HTML; only explicit <br> separators and **bold** are interpreted.
    tokens = re.split(r'(\\[\\|*]|<br\s*/?>|\*\*[^\n]+?\*\*)', text, flags=re.I)
    output = []
    for token in tokens:
        if re.fullmatch(r'<br\s*/?>', token, re.I):
            output.append('<br>')
        elif token.startswith('\\') and len(token) == 2:
            output.append(escape(token[1]))
        elif token.startswith('**') and token.endswith('**') and len(token) > 4:
            output.append('<strong>' + escape(token[2:-2]).replace('\\|', '|') + '</strong>')
        else:
            output.append(escape(token))
    return ''.join(output)


def render_cell(text):
    chunks = re.split(r'<br\s*/?>', text, flags=re.I)
    if chunks and all(re.match(r'^\d+[.)]\s+', part.strip()) for part in chunks):
        first = int(re.match(r'^(\d+)', chunks[0].strip())[1])
        if first != 1:
            raise ConversionError('Ordered lists inside table cells must start at 1.')
        return '<ol>' + ''.join(
            '<li>' + inline(re.sub(r'^\d+[.)]\s+', '', part.strip())) + '</li>'
            for part in chunks
        ) + '</ol>'
    return inline(text)


def render_markdown(source):
    lines = source.splitlines()
    blocks, index, tables, rows = [], 0, 0, 0
    while index < len(lines):
        line = lines[index].strip()
        number = index + 1
        if not line:
            index += 1
            continue
        if line.startswith(('```', '~~~')):
            raise ConversionError(f'Line {number}: fenced code blocks are outside this PRD converter.')
        heading = re.match(r'^(#{1,6})\s+(.*)$', line)
        if heading:
            level = len(heading[1])
            blocks.append(f'<h{level}>' + inline(heading[2]) + f'</h{level}>')
            index += 1
        elif line.startswith('|'):
            table_rows = []
            while index < len(lines) and lines[index].strip().startswith('|'):
                try:
                    table_rows.append(split_row(lines[index]))
                except ConversionError as error:
                    raise ConversionError(f'Line {index + 1}: {error}') from error
                index += 1
            if len(table_rows) < 2 or not all(re.fullmatch(r':?-{3,}:?', cell) for cell in table_rows[1]):
                raise ConversionError(f'Line {number}: missing Markdown table separator.')
            headers = table_rows[0]
            if len(table_rows[1]) != len(headers):
                raise ConversionError(f'Line {number}: separator column count differs from header.')
            tables += 1
            kind = 'requirements' if headers == ['功能项', '描述', '图例'] else 'reference'
            head = ''.join('<th scope="col">' + inline(value) + '</th>' for value in headers)
            body = []
            for offset, values in enumerate(table_rows[2:], start=2):
                if len(values) != len(headers):
                    raise ConversionError(f'Line {number + offset}: expected {len(headers)} cells, found {len(values)}.')
                rows += 1
                cells = ''.join('<td>' + render_cell(value) + '</td>' for value in values)
                label = escape('复制本行：' + values[0], quote=True)
                button = f'<td class="copy-control"><button type="button" class="copy-row" aria-label="{label}">复制本行</button></td>'
                body.append('<tr>' + cells + button + '</tr>')
            blocks.append(
                f'<div class="table-wrap"><table class="{kind}" data-source-columns="{len(headers)}">'
                '<thead><tr>' + head + '<th class="copy-control" scope="col">操作</th></tr></thead>'
                '<tbody>' + ''.join(body) + '</tbody></table></div>'
            )
        elif re.match(r'^\d+[.)]\s+', line):
            start = int(re.match(r'^(\d+)', line)[1])
            items = []
            while index < len(lines) and re.match(r'^\d+[.)]\s+', lines[index].strip()):
                items.append('<li>' + inline(re.sub(r'^\d+[.)]\s+', '', lines[index].strip())) + '</li>')
                index += 1
            blocks.append(f'<ol start="{start}">' + ''.join(items) + '</ol>')
        else:
            paragraph = [line]
            index += 1
            while index < len(lines) and lines[index].strip() and not re.match(r'^(#|\||\d+[.)]\s|```|~~~)', lines[index].strip()):
                paragraph.append(lines[index].strip())
                index += 1
            blocks.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(blocks), {'tables': tables, 'rows': rows}


def convert(source, title):
    body, stats = render_markdown(source)
    template = (Path(__file__).resolve().parent.parent / 'assets' / 'row-copy.html').read_text(encoding='utf-8')
    return template.replace('__TITLE__', escape(title)).replace('__CONTENT__', body), stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='UTF-8 Markdown source (kept unchanged)')
    parser.add_argument('-o', '--output', type=Path, help='HTML output; defaults to input with .html extension')
    parser.add_argument('--title', help='Display title; defaults to input filename stem')
    parser.add_argument('--force', action='store_true', help='Replace an existing HTML output')
    args = parser.parse_args()
    target = args.output or args.input.with_suffix('.html')
    if target.resolve() == args.input.resolve():
        parser.error('Input and output paths must differ.')
    if target.exists() and not args.force:
        parser.error('Output already exists. Choose another path or use --force when replacement is intended.')
    try:
        result, stats = convert(args.input.read_text(encoding='utf-8-sig'), args.title or args.input.stem)
    except (OSError, ConversionError) as error:
        parser.exit(2, f'Conversion failed: {error}\n')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result, encoding='utf-8')
    print(f'Created {target}: {stats["tables"]} tables, {stats["rows"]} copyable rows.')


if __name__ == '__main__':
    main()
