"""Deterministic, stateless billing analysis. Money never passes through floats."""
import csv
import io
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256

MAX_BYTES = 1024 * 1024
MAX_RECORDS = 10000
MAX_FIELD = 512
csv.field_size_limit(4096)

class AnalysisError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message

def fail(code, message):
    raise AnalysisError(code, message)

def money(value):
    text = str(value).strip().replace(',', '')
    if text.startswith('(') and text.endswith(')'):
        text = '-' + text[1:-1]
    try:
        amount = Decimal(text)
    except InvalidOperation:
        fail('INVALID_AMOUNT', f'Invalid monetary value: {str(value)[:40]!r}.')
    if not amount.is_finite() or abs(amount) > Decimal('1000000000000') or amount.as_tuple().exponent < -12:
        fail('INVALID_AMOUNT', 'Amounts must be finite numbers with at most 12 decimal places.')
    return amount

def iso_date(value, date_order=''):
    text = value.strip()
    if not text:
        return None, 'unspecified'
    if re.fullmatch(r'\d{4}-\d{2}', text):
        try:
            date.fromisoformat(text + '-01')
        except ValueError:
            fail('INVALID_DATE', f'Invalid month: {text}.')
        return text, 'monthly'
    try:
        return date.fromisoformat(text[:10]).isoformat(), 'daily'
    except ValueError:
        pass
    match = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if match and date_order in ('DMY', 'MDY'):
        a, b, y = map(int, match.groups())
        try:
            return date(y, b if date_order == 'DMY' else a, a if date_order == 'DMY' else b).isoformat(), 'daily'
        except ValueError:
            pass
    fail('INVALID_DATE', f'Date {text!r} needs ISO YYYY-MM-DD or an explicit DMY/MDY selection.')

def parse_table(raw):
    if len(raw) > MAX_BYTES:
        fail('FILE_TOO_LARGE', 'Upload at most 1 MiB across both files.')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        fail('INVALID_CSV', 'Use a UTF-8 CSV export.')
    if '\x00' in text:
        fail('INVALID_CSV', 'This does not look like a text CSV.')
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel
    try:
        records = list(csv.reader(io.StringIO(text), dialect))
    except csv.Error:
        fail('INVALID_CSV', 'The CSV contains malformed quoting or an oversized field.')
    records = [(n + 1, r) for n, r in enumerate(records) if any(c.strip() for c in r)]
    if len(records) < 2:
        fail('INVALID_CSV', 'Include a header and at least one data record.')
    headers = [h.strip() for h in records[0][1]]
    if len(set(h.lower() for h in headers)) != len(headers):
        fail('DUPLICATE_HEADERS', 'Column names must be unique.')
    if len(headers) > 100 or any(len(h) > MAX_FIELD for h in headers):
        fail('INVALID_CSV', 'Use at most 100 columns and short column names.')
    for n, row in records[1:]:
        if len(row) != len(headers):
            fail('INVALID_CSV', f'CSV record {n} has {len(row)} cells; expected {len(headers)}.')
        if any(len(c) > MAX_FIELD for c in row):
            fail('INVALID_CSV', f'CSV record {n} has a field longer than {MAX_FIELD} characters.')
    if len(records) - 1 > MAX_RECORDS:
        fail('TOO_MANY_RECORDS', 'Use at most 10,000 records.')
    return headers, records[1:]

ALIASES = {
    'service': ['service','product','product name','lineitem/productcode'],
    'cost': ['cost','amount','unblended cost','unblendedcost','lineitem/unblendedcost'],
    'date': ['date','period','month','usage date','lineitem/usagestartdate'],
    'currency': ['currency','currency code','lineitem/currencycode'],
    'region': ['region','product/region','product/regioncode'],
    'charge_type': ['charge type','type','lineitem/lineitemtype'],
}

def detect(headers):
    lookup = {h.lower(): h for h in headers}
    mapping = {field: next((lookup[a] for a in aliases if a in lookup), '') for field, aliases in ALIASES.items()}
    dates = [h for h in headers if re.fullmatch(r'\d{4}-\d{2}(-\d{2})?', h)]
    kind = 'cur' if 'lineitem/unblendedcost' in lookup else 'generic'
    if dates and not mapping['cost']:
        kind = 'cost_explorer_wide'
        if not mapping['service']:
            mapping['service'] = headers[0]
    return kind, mapping, dates

def inspect(raw):
    headers, table = parse_table(raw)
    kind, mapping, dates = detect(headers)
    return {'headers': headers, 'preview': [dict(zip(headers, row)) for _, row in table[:5]], 'format': kind, 'mapping': mapping, 'record_count': len(table), 'date_columns': dates}

def parse(raw, filename, options=None, role='current'):
    options = options or {}
    headers, table = parse_table(raw)
    kind, detected, date_cols = detect(headers)
    mapping = detected | {k: v for k, v in options.get('mapping', {}).items() if k in ALIASES}
    if not mapping['service'] or (kind != 'cost_explorer_wide' and not mapping['cost']):
        fail('MISSING_COLUMNS', 'Map the service and cost columns before analyzing.')
    for col in mapping.values():
        if col and col not in headers:
            fail('MISSING_COLUMNS', f'Column {col!r} is not present in {filename}.')
    currency_default = options.get('currency', '').strip().upper()
    if currency_default and not re.fullmatch('[A-Z]{3}', currency_default):
        fail('INVALID_CURRENCY', 'Use a three-letter currency code such as USD.')
    basis = 'unblended' if kind == 'cur' else options.get('cost_basis', 'exported').strip()
    if basis not in ('exported', 'unblended', 'amortized'):
        fail('INVALID_BASIS', 'Select exported, unblended, or amortized cost.')
    file_id = sha256(raw).hexdigest()[:12] + '-' + role
    output, excluded, seen, duplicates = [], [], set(), 0
    for n, cells in table:
        row = dict(zip(headers, cells))
        get = lambda field: row.get(mapping.get(field, ''), '').strip()
        service = get('service')
        if service.lower() in ('total', 'grand total', 'service total', 'total costs', 'total cost'):
            excluded.append(n)
            continue
        if not service:
            fail('INVALID_CSV', f'CSV record {n} is missing a service.')
        if tuple(cells) in seen:
            duplicates += 1
        seen.add(tuple(cells))
        currency = get('currency').upper() or currency_default
        if not re.fullmatch('[A-Z]{3}', currency):
            fail('MISSING_CURRENCY', 'Choose the currency shown in your export; BillSense will not assume one.')
        entries = [(h, row[h], h) for h in date_cols] if kind == 'cost_explorer_wide' else [(get('date'), get('cost'), mapping['cost'])]
        for d, value, source_column in entries:
            if value.strip() == '':
                fail('INVALID_AMOUNT', f'CSV record {n}, column {source_column!r} has a blank cost.')
            try:
                amount = money(value)
                day, granularity = iso_date(d, options.get('date_order', ''))
            except AnalysisError as exc:
                fail(exc.code, f'Record {n}: {exc.message}')
            output.append({'record_id': f'{file_id}-{n}-{len(output)}', 'source_file_id': file_id,
                'source_file': filename[:120], 'source_record_number': n, 'source_column_name': source_column,
                'service': service, 'amount_decimal': str(amount), 'currency': currency,
                'date': day, 'granularity': granularity, 'region': get('region') or 'Unknown',
                'charge_type': get('charge_type') or 'Unspecified', 'cost_basis': basis, 'role': role})
            if len(output) > MAX_RECORDS:
                fail('TOO_MANY_RECORDS', 'Wide CSV expansion exceeds 10,000 normalized records.')
    if not output:
        fail('INVALID_CSV', 'No billable detail records were found.')
    if len({r['currency'] for r in output}) != 1:
        fail('MIXED_CURRENCY', 'Analyze each currency separately; currency conversion is not supported.')
    warnings = []
    if excluded:
        warnings.append(f'Excluded {len(excluded)} explicitly labeled total records: ' + ', '.join(map(str, excluded[:10])) + '.')
    if kind == 'cost_explorer_wide':
        warnings.append('Only ISO-date columns were analyzed. Summary and other non-date columns were excluded.')
    if duplicates:
        warnings.append(f'{duplicates} duplicate-looking records were retained; verify they belong in your export.')
    if any(r['region'] == 'Unknown' for r in output):
        warnings.append('Some records have no region; these are grouped as Unknown.')
    if any(r['date'] is None for r in output):
        warnings.append('Some records have no date; no complete time-series coverage can be established.')
    dates = sorted({r['date'] for r in output if r['date']})
    label = options.get('period_label', '').strip()[:80] or (f'{dates[0]} – {dates[-1]}' if len(dates) > 1 else dates[0] if dates else 'Period not specified')
    return output, {'filename': filename, 'format': kind, 'period': label, 'cost_basis': basis, 'currency': output[0]['currency'], 'warnings': warnings, 'excluded_records': excluded}

CATALOG = {
    'EC2': {'title': 'Review EC2 usage and attached resources', 'detail': 'Check instance running hours, attached EBS volumes, snapshots, and public IPv4 charges. Confirm ownership and workload needs before changing anything.', 'url': 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Using_Tags.html'},
    'S3': {'title': 'Check S3 storage classes and requests', 'detail': 'Review stored bytes, request counts, retrievals, and lifecycle policies. A bill alone cannot show whether an object is still needed.', 'url': 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html'},
    'RDS': {'title': 'Review database hours, storage, and backups', 'detail': 'Inspect database instance hours, storage allocation, and retained backups. Check application dependencies before resizing or stopping a database.', 'url': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.html'},
    'Lambda': {'title': 'Inspect function invocations and duration', 'detail': 'Review invocation volume, duration, memory settings, and retry behavior in function metrics.', 'url': 'https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html'},
    'Transfer': {'title': 'Inspect data transfer paths', 'detail': 'Check usage types to distinguish internet, cross-region, and other transfer charges. Aggregate costs do not identify the exact traffic source.', 'url': 'https://docs.aws.amazon.com/cost-management/latest/userguide/ce-filtering.html'},
    'Other': {'title': 'Inspect this service in Cost Explorer', 'detail': 'Filter by service, usage type, and region to understand which activity produced these charges. Confirm resource-level details in the AWS console.', 'url': 'https://docs.aws.amazon.com/cost-management/latest/userguide/ce-filtering.html'},
}

def category(service):
    s = service.lower()
    for token, key in [('ec2','EC2'),('elastic compute','EC2'),('s3','S3'),('simple storage','S3'),('rds','RDS'),('relational database','RDS'),('lambda','Lambda'),('transfer','Transfer')]:
        if token in s:
            return key
    return 'Other'

def summarize(records, meta, previous=None, previous_meta=None, sample=False):
    zero = Decimal('0')
    amounts = [Decimal(r['amount_decimal']) for r in records]
    net, positive, negative = sum(amounts, zero), sum((a for a in amounts if a > 0), zero), sum((a for a in amounts if a < 0), zero)
    services, positives, regions, daily = defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal)
    for r in records:
        a = Decimal(r['amount_decimal'])
        services[r['service']] += a
        positives[r['service']] += max(a, zero)
        regions[r['region']] += a
        if r['granularity'] == 'daily':
            daily[r['date']] += a
    old = defaultdict(Decimal)
    comparison = None
    warnings = list(meta['warnings'])
    if previous:
        if meta['currency'] != previous_meta['currency']:
            fail('MIXED_CURRENCY', 'Both periods must use the same currency.')
        if meta['cost_basis'] != previous_meta['cost_basis']:
            fail('INCOMPATIBLE_COMPARISON', 'Both periods must use the same cost basis.')
        for r in previous:
            old[r['service']] += Decimal(r['amount_decimal'])
        prior = sum(old.values(), zero)
        delta = net - prior
        comparison = {'previous_total': str(prior), 'change': str(delta), 'percentage': str(delta / prior * 100) if prior > 0 else None, 'previous_period': previous_meta['period'], 'previous_meta': previous_meta}
        warnings += ['Comparison uses the complete selected exports. Equal duration and completeness are not assumed.']
        warnings += [f'Previous period: {w}' for w in previous_meta['warnings']]
    service_rows = [{'name': s, 'cost': str(services[s]), 'positive': str(positives[s]), 'share': str(positives[s]/positive*100) if positive else '0', 'previous': str(old[s]) if previous else None, 'change': str(services[s]-old[s]) if previous else None} for s in set(services) | set(old)]
    service_rows.sort(key=lambda r: Decimal(r['positive']), reverse=True)
    findings = []
    for idx, item in enumerate(service_rows[:5]):
        s = item['name']
        evidence = [r['record_id'] for r in records if r['service'] == s]
        old_evidence = [r['record_id'] for r in (previous or []) if r['service'] == s]
        findings.append({'id': f'finding-{idx}', 'service': s, 'title': f'{s} spending', 'amount': item['cost'], 'share': item['share'], 'change': item['change'], 'evidence_ids': evidence, 'previous_evidence_ids': old_evidence, 'next_step': category(s), 'classification': 'Observed in your data'})
    daily_enabled = all(r['granularity'] == 'daily' for r in records)
    return {'schema_version': '1.0', 'sample': sample, 'meta': meta, 'warnings': warnings, 'metrics': {'net': str(net), 'positive': str(positive), 'negative': str(negative), 'record_count': len(records), 'service_count': len(services)}, 'services': service_rows, 'regions': [{'name': s, 'cost': str(c)} for s,c in sorted(regions.items(), key=lambda x: x[1], reverse=True)], 'daily': [{'date': d, 'cost': str(c)} for d,c in sorted(daily.items())] if daily_enabled else [], 'comparison': comparison, 'findings': findings, 'records': records + (previous or []), 'next_steps': [{'id': k, **v} for k,v in CATALOG.items() if k in {f['next_step'] for f in findings}], 'explanation_mode': 'calculated'}

def analyze_files(files, options=None, sample=False):
    if sum(len(raw) for raw, _ in files) > MAX_BYTES:
        fail('FILE_TOO_LARGE', 'Upload at most 1 MiB across both files.')
    if len(files) == 2 and files[0][0] == files[1][0]:
        fail('DUPLICATE_FILE', 'Choose a different previous-period file.')
    options = options or {}
    records, meta = parse(*files[0], options.get('current', {}), 'current')
    previous, prev_meta = (None, None)
    if len(files) == 2:
        previous, prev_meta = parse(*files[1], options.get('previous', {}), 'previous')
    if len(records) + len(previous or []) > MAX_RECORDS:
        fail('TOO_MANY_RECORDS', 'Use at most 10,000 normalized records across both files.')
    return summarize(records, meta, previous, prev_meta, sample)
