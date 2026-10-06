"""Validate and bind the one active TGI manuscript and rendered PDF."""
from pathlib import Path
import hashlib
import json
import re

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/technical/TGI_TOPOLOGICAL_GEOMETRIC_INTELLIGENCE.md'
PDF = PAPER.with_suffix('.pdf')
MANIFEST = PAPER.parent / 'validation.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = PAPER.read_text(encoding='utf-8')
    pdf = PdfReader(str(PDF))
    extracted = '\n'.join(page.extract_text() or '' for page in pdf.pages)
    if source.count('# TGI: Topological Geometric Intelligence\n') != 1:
        raise ValueError('Exactly one active title required')
    if source.count('## Abstract\n') != 1 or source.count('## References\n') != 1:
        raise ValueError('One abstract and bibliography required')
    if source.count('\n4 October 2026\n') != 1:
        raise ValueError('Original paper date must be 4 October 2026')
    for term in ('KONSEP.txt', 'FOUNDATION_DRAFT', 'HIPOTESIS',
                 '## References\n\n[', 'companion paper'):
        if term in source or term in extracted:
            raise ValueError(f'Internal working label in publication: {term}')
    if re.search(r'\[\d+(?:[,–-]\d+)*\]', source):
        raise ValueError('Unmapped numerical citation')
    records = ('7341318', '7341819', '7345360', '7355679')
    if any(source.count(f'abstract_id={record}') != 1 or
           f'abstract_id={record}' not in extracted for record in records):
        raise ValueError('Bibliography record missing or duplicated')
    result = {
        'revision': 'TGI-UNIFIED-ARTICLE-20261004',
        'paper_date': '2026-10-04',
        'title': 'TGI: Topological Geometric Intelligence',
        'author': 'Emylton Leunufna',
        'source_sha256': digest(PAPER),
        'pdf_sha256': digest(PDF),
        'pages': len(pdf.pages),
        'source_words': len(re.findall(r'\b\w+\b', source)),
        'scientific_references': 4,
        'predecessor_git_revision': 'de95c4c',
        'predecessor_manuscript_count': 6,
        'cited_code_revision': 'de95c4c',
        'cited_package_version': '0.2.0.dev0',
        'submitted_predecessors_preserved_in_prior_git_revision': True,
    }
    MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    print(json.dumps({'passed': True, 'pages': result['pages'],
                      'source_sha256': result['source_sha256'],
                      'pdf_sha256': result['pdf_sha256']}))


if __name__ == '__main__':
    main()
