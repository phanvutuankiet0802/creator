"""Source-bound objective inventory gate; technical integrity, not medical peer review.

One inventory may have candidates. It cannot self-attest complete coverage or validate
clinical truth. All selected sources require real bytes and source quotes. All P0/P1
objectives need traceable product planning, but mappings alone do not prove pedagogy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _safe_file(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        raise ValueError('INVALID_SOURCE_PATH')
    p = (root / rel).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError('SOURCE_NOT_FOUND_OR_OUTSIDE_ROOT')
    return p


def assess(inventory: dict[str, Any], root: Path) -> dict[str, Any]:
    errors: list[str] = []
    reviews: list[str] = []
    registry = inventory.get('source_registry', {})
    selected = inventory.get('selected_source_ids', [])
    records = inventory.get('proposed_objectives', [])
    contents = {}
    if not isinstance(registry, dict) or not isinstance(selected, list) or not selected:
        errors.append('MISSING_SELECTED_SOURCE_REGISTRY')
    else:
        for source_id in selected:
            entry = registry.get(source_id)
            if not isinstance(entry, dict):
                errors.append(f'SOURCE_MISSING:{source_id}')
                continue
            try:
                path = _safe_file(root, entry.get('path'))
                raw = path.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                if digest != entry.get('sha256'):
                    errors.append(f'SOURCE_HASH_MISMATCH:{source_id}')
                    continue
                contents[source_id] = raw.decode('utf-8')
            except (ValueError, UnicodeDecodeError, OSError, TypeError) as exc:
                errors.append(f'INVALID_SOURCE:{source_id}:{type(exc).__name__}')
            if not entry.get('faculty_approval_verified'):
                reviews.append(f'NO_VERIFIED_FACULTY_APPROVAL:{source_id}')
    if not isinstance(records, list) or not records:
        errors.append('NO_OBJECTIVE_INVENTORY')
        records = []
    seen = set()
    priority_counts = {'P0':0,'P1':0,'P2':0,'P3':0,'P4':0}
    risk_ids = []
    for item in records:
        if not isinstance(item, dict):
            errors.append('INVALID_OBJECTIVE');continue
        ident = item.get('id')
        if not isinstance(ident, str) or not ident or ident in seen:
            errors.append(f'DUPLICATE_OR_EMPTY_ID:{ident}')
            continue
        seen.add(ident)
        pr = item.get('priority_proposed')
        if pr not in priority_counts:
            errors.append(f'INVALID_PRIORITY:{ident}')
        else:
            priority_counts[pr] += 1
        sid = item.get('source')
        if sid not in selected:
            errors.append(f'UNSELECTED_SOURCE:{ident}')
            continue
        body = contents.get(sid)
        quote = item.get('source_quote')
        if body is None:
            errors.append(f'UNVERIFIABLE_SOURCE:{ident}')
        elif not isinstance(quote,str) or not quote.strip() or quote not in body:
            errors.append(f'QUOTE_NOT_IN_SOURCE:{ident}')
        else:
            line = item.get('source_line')
            lines = body.splitlines()
            if not isinstance(line,int) or line < 1 or line > len(lines) or quote not in lines[line-1]:
                errors.append(f'INCORRECT_SOURCE_LINE:{ident}')
        output = item.get('output_expectation', {})
        if not isinstance(output,dict) or any(key not in output for key in ('lecture','flashcard','mcq','meq')):
            errors.append(f'MISSING_FOUR_PRODUCT_PLAN:{ident}')
        if pr in ('P0','P1') and output.get('lecture') in ('none', 'brief', None):
            errors.append(f'CRITICAL_LECTURE_DOWNGRADED:{ident}')
        if item.get('clinical_claim_risk'):
            risk_ids.append(ident)
            if item.get('evidence_review') != 'APPROVED_BY_VERIFIED_MEDICAL_REVIEW':
                reviews.append(f'CLINICAL_REVIEW_PENDING:{ident}')
        if item.get('priority_approval') != 'APPROVED_BY_VERIFIED_REVIEW':
            reviews.append(f'PRIORITY_REVIEW_PENDING:{ident}')
    if not inventory.get('inventory_completeness_verified'):
        reviews.append('INVENTORY_COMPLETENESS_UNVERIFIED')
    if not inventory.get('all_critical_objectives_verified'):
        reviews.append('CRITICAL_OBJECTIVES_UNVERIFIED')
    if not inventory.get('international_medical_review_verified'):
        reviews.append('INTERNATIONAL_RECONCILIATION_PENDING')
    if inventory.get('learner_facing_pdf_citations'):
        errors.append('PDF_CITATION_CONTRACT_VIOLATION')
    # Marked reviewed=true in untrusted JSON is not accepted as reviewer identity/trust-root.
    if inventory.get('self_certified_release'):
        errors.append('UNTRUSTED_RELEASE_SELF_CERTIFICATION')
    return {'status': 'BLOCKED_INTEGRITY' if errors else 'HOLD_FOR_ACADEMIC_REVIEW',
            'technical_valid': not errors, 'academic_certified': False, 'release_allowed': False,
            'objective_count':len(records), 'priority_counts':priority_counts,
            'high_risk_count':len(risk_ids),'high_risk_ids':risk_ids,
            'integrity_errors':errors,'review_requirements':sorted(set(reviews))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('inventory')
    parser.add_argument('--root',required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    inv = json.loads(Path(args.inventory).read_text(encoding='utf-8'))
    result = assess(inv,Path(args.root))
    data = json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        Path(args.output).write_text(data,encoding='utf-8')
    print(data)
    return 2 if result['integrity_errors'] else 0

if __name__=='__main__':
    raise SystemExit(main())
