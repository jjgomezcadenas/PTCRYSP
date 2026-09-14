#!/usr/bin/env python3
"""Calculate CSV models, export Excel and generate/check one slide per table.

Inputs and formulas live in CSV, not in this script. Formula expressions support
row identifiers, arithmetic, round(value, digits), and ceil(value).
"""
from __future__ import annotations

import argparse
import ast
import csv
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
TABLES = ('installation', 'installation_market', 'annual_service', 'recurring_market', 'market_growth', 'argos_market', 'costs-reduced', 'startup_team', 'startup_programme')
TOKEN = re.compile(r'\{\{([a-z_]+)\|([a-z0-9]+)\}\}')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def load_model(directory=ROOT, table_names=TABLES):
    tables, rows, values, cells = {}, {}, {}, {}
    for name in table_names:
        with (Path(directory) / f'{name}.csv').open(newline='') as f:
            tables[name] = list(csv.DictReader(f))
        for index, row in enumerate(tables[name], 2):
            key = row['id']
            if not re.fullmatch(r'[a-z_]+', key) or key in rows:
                raise ValueError(f'Invalid or duplicate ID: {key}')
            if bool(row['value'].strip()) == bool(row['formula'].strip()):
                raise ValueError(f'{key}: provide exactly one value or formula')
            rows[key] = row
            cells[key] = f"'{name}'!D{index}"
    visiting = set()

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            return resolve(node.id)
        if isinstance(node, ast.BinOp):
            a, b = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
            if isinstance(node.op, ast.Pow): return a ** b
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -evaluate(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            args = [evaluate(arg) for arg in node.args]
            if node.func.id == 'round' and len(args) == 2:
                return float(Decimal(str(args[0])).quantize(Decimal(10) ** -int(args[1]), rounding=ROUND_HALF_UP))
            if node.func.id == 'ceil' and len(args) == 1: return math.ceil(args[0])
        raise ValueError(f'Unsupported expression: {ast.dump(node)}')

    def resolve(key):
        if key in values: return values[key]
        if key in visiting: raise ValueError(f'Circular formula at {key}')
        if key not in rows: raise ValueError(f'Unknown formula ID: {key}')
        visiting.add(key)
        row = rows[key]
        value = evaluate(ast.parse(row['formula'], mode='eval').body) if row['formula'] else float(row['value'])
        if not math.isfinite(value) or (not row['formula'] and value < 0):
            raise ValueError(f'{key}: input must be finite and nonnegative, got {value}')
        if not row['formula'] and row['unit'] == 'fraction' and value > 1:
            raise ValueError(f'{key}: fraction must be between zero and one')
        if key == 'other_raw' and value < 0:
            raise ValueError('Raw hardware budget is smaller than PET plus camera costs')
        values[key] = value
        visiting.remove(key)
        return value

    for key in rows: resolve(key)
    return tables, rows, values, cells


def excel_expression(expression, cells):
    def convert(node):
        if isinstance(node, ast.Constant): return str(node.value)
        if isinstance(node, ast.Name): return cells[node.id]
        if isinstance(node, ast.BinOp):
            op = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Pow: '^'}[type(node.op)]
            return f'({convert(node.left)}{op}{convert(node.right)})'
        if isinstance(node, ast.UnaryOp): return f'(-{convert(node.operand)})'
        if isinstance(node, ast.Call):
            args = ','.join(convert(arg) for arg in node.args)
            return f'ROUND({args})' if node.func.id == 'round' else f'CEILING({args},1)'
        raise ValueError(expression)
    return '=' + convert(ast.parse(expression, mode='eval').body)


def write_workbook(tables, values, cells):
    import xlsxwriter
    with xlsxwriter.Workbook(ROOT / 'costs.xlsx', {'strings_to_urls': False}) as book:
        book.set_properties({'title': 'ARGOS installation and service economics',
                             'comments': 'Generated from CSV tables. Edit CSV, then regenerate.'})
        normal = book.add_format({'num_format': '#,##0.00;[Red]-#,##0.00'})
        fraction = book.add_format({'num_format': '0.0%'})
        input_fmt = book.add_format({'font_color': '#1565C0', 'num_format': '#,##0.00'})
        input_fraction = book.add_format({'font_color': '#1565C0', 'num_format': '0.0%'})
        for name, rows in tables.items():
            sheet = book.add_worksheet(name)
            sheet.freeze_panes(1, 2)
            sheet.set_column('A:A', 28)
            sheet.set_column('B:B', 57)
            sheet.set_column('C:C', 12)
            sheet.set_column('D:D', 20)
            sheet.set_column('E:E', 15)
            sheet.set_column('F:F', 57)
            sheet.set_column('G:G', 100)
            sheet.add_table(0, 0, len(rows), 6, {
                'name': f"model_{name.replace('-', '_')}", 'style': 'Table Style Medium 2',
                'columns': [{'header': h} for h in ['ID', 'Item', 'Kind', 'Value', 'Unit', 'Calculation', 'Assumption / source']]})
            for index, row in enumerate(rows, 1):
                key = row['id']
                sheet.write_row(index, 0, [key, row['label'], 'Derived' if row['formula'] else 'Input'])
                if row['formula']:
                    sheet.write_formula(index, 3, excel_expression(row['formula'], cells),
                                        fraction if row['unit'] == 'fraction' else normal, values[key])
                else:
                    sheet.write_number(index, 3, values[key], input_fraction if row['unit'] == 'fraction' else input_fmt)
                sheet.write_row(index, 4, [row['unit'], row['formula'], row['notes']])


def formatted(value, fmt):
    if fmt == 'y': return str(int(value))
    if fmt == 'n': return f'{value:,.0f}' if value == int(value) else f'{value:,.2f}'.rstrip('0').rstrip('.')
    if fmt == 'k': return f'{value / 1000:,.0f}' if value % 1000 == 0 else f'{value / 1000:,.1f}'
    if re.fullmatch(r'm[012]', fmt): return f'{value / 1e6:,.{fmt[1]}f}'
    if fmt == 'p': return f'{100 * value:.0f}' if math.isclose(100 * value, round(100 * value), abs_tol=1e-10) else f'{100 * value:.1f}'
    if fmt == 'p1': return f'{100 * value:.1f}'
    if fmt == 'k1': return f'{value / 1000:,.1f}'
    raise ValueError(f'Unknown number format: {fmt}')


def render(values):
    slides, expected = [], {}
    for name in TABLES:
        template = (ROOT / f'{name}.tex.in').read_text()
        if template.count(r'\begin{frame}') != 1 or template.count(r'\end{frame}') != 1:
            raise ValueError(f'{name}: exactly one frame required')
        expected[name] = []
        def substitute(match):
            key, fmt = match.groups()
            text = formatted(float(values[key]), fmt)
            return text
        # Commented-out notes are generated, but are not visible in the PDF.
        # Preserve escaped percent signs used in rendered percentages.
        for line in template.splitlines():
            visible = re.split(r'(?<!\\)%', line, maxsplit=1)[0]
            for match in TOKEN.finditer(visible):
                key, fmt = match.groups()
                expected[name].append({'id': key, 'format': fmt,
                                       'display': formatted(float(values[key]), fmt)})
        slide = TOKEN.sub(substitute, template)
        if '{{' in slide: raise ValueError(f'Unresolved placeholder in {name}')
        slides.append(f'% Generated from {name}.csv and {name}.tex.in; do not edit.\n' + slide)
    return '\n'.join(slides), expected


def check_workbook(tables, values, cells):
    with zipfile.ZipFile(ROOT / 'costs.xlsx') as archive:
        strings = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        shared = [''.join(node.itertext()) for node in strings.findall('m:si', NS)]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        names = [node.attrib['name'] for node in workbook.findall('m:sheets/m:sheet', NS)]
        assert names == list(TABLES), 'Workbook sheets do not match CSV tables'
        assert len([name for name in archive.namelist() if re.fullmatch(r'xl/tables/table\d+\.xml', name)]) == len(TABLES)
        for index, (name, rows) in enumerate(tables.items(), 1):
            sheet = ET.fromstring(archive.read(f'xl/worksheets/sheet{index}.xml'))
            data = {node.attrib['r']: node for node in sheet.findall('.//m:c', NS)}
            for row in rows:
                key = row['id']
                address = cells[key].split('!')[1]
                cell = data[address]
                cached = float(cell.find('m:v', NS).text)
                assert math.isclose(cached, values[key], rel_tol=1e-10, abs_tol=1e-7), key
                if row['formula']:
                    assert '=' + cell.find('m:f', NS).text == excel_expression(row['formula'], cells), key
                for column, text in zip('ABCEFG', [key, row['label'], 'Derived' if row['formula'] else 'Input', row['unit'], row['formula'], row['notes']]):
                    node = data.get(column + address[1:])
                    actual = shared[int(node.find('m:v', NS).text)] if node is not None and node.attrib.get('t') == 's' else ''
                    assert actual == text, f'{key}: stale Excel metadata in column {column}'


def check_pdf(pdf, expected):
    text = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
    pages = text.split('\f')
    result = {}
    for name in TABLES:
        title = re.search(r'\\begin\{frame\}\{([^}]+)\}', (ROOT / f'{name}.tex.in').read_text()).group(1)
        found = [(i + 1, page) for i, page in enumerate(pages) if title in ' '.join(page.split())]
        if len(found) != 1: raise ValueError(f'{name}: expected one PDF page, found {len(found)}')
        page_number, page = found[0]
        for item in expected[name]:
            pattern = r'(?<![\d.,])' + re.escape(item['display']) + r'(?!\d|[.,]\d)'
            if not re.search(pattern, page):
                raise ValueError(f"PDF page {page_number}: missing {item['id']} = {item['display']}")
        result[name] = page_number
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check existing generated artifacts instead of replacing them')
    parser.add_argument('--pdf', type=Path, help='Also verify each model number displayed in the compiled PDF')
    args = parser.parse_args()
    tables, rows, values, cells = load_model()
    tex, expected = render(values)
    payload = json.dumps({'values': values, 'slides': expected}, indent=2) + '\n'
    outputs = {'slides.tex': tex, 'calculated.json': payload}
    for name, slide in zip(TABLES, tex.split('\n% Generated from ')):
        outputs[f'slides/{name}.tex'] = slide if slide.startswith('% Generated from ') else '% Generated from ' + slide
    (ROOT / 'slides').mkdir(exist_ok=True)
    if args.check:
        for name, content in outputs.items():
            if (ROOT / name).read_text() != content:
                raise ValueError(f'{name} is stale; run build_costs.py')
    else:
        for name, content in outputs.items(): (ROOT / name).write_text(content)
        write_workbook(tables, values, cells)
    check_workbook(tables, values, cells)
    main_tex = (ROOT.parent / 'pbt_argos.tex').read_text()
    block = main_tex.count(r'\input{costs/slides.tex}')
    per_slide = [main_tex.count('\\input{costs/slides/%s.tex}' % name) for name in TABLES]
    assert (block == 1 and not any(per_slide)) or (block == 0 and all(n == 1 for n in per_slide)), \
        'Deck must include the model slides exactly once: either costs/slides.tex or every costs/slides/<table>.tex'
    assert tex.count(r'\begin{frame}') == len(tables) == len(TABLES)
    pdf_pages = check_pdf(args.pdf, expected) if args.pdf else {}
    lines = ['# Cost model consistency report', '',
             f'- PASS: {len(TABLES)} CSV tables, Excel sheets/named tables and generated slides.',
             f'- PASS: all {len(rows)} input/derived values match Excel cached values; formulas match Python expressions.',
             '- PASS: all displayed model numbers are generated from the CSV calculation model.',
             '- PASS: deck includes the generated slides exactly once.',
             '- Scope: the generated economics and market slides; unrelated clinical and market-survey slides are outside this audit.']
    if pdf_pages:
        lines += [f'- PASS: {name}: rendered PDF page {page}; all model number strings found.' for name, page in pdf_pages.items()]
        lines += ['- PDF matching checks displayed numbers and titles, not layout; visual review remains a separate step.']
    else:
        lines += ['- PDF not checked in this run. Rebuild the talk, then run with --check --pdf ../pbt_argos.pdf.']
    (ROOT / 'consistency_report.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
