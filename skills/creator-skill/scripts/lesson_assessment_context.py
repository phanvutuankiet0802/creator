#!/usr/bin/env python3
"""Lesson-aware assessment probe. Structural/trace checks, never semantic certification.

Legacy NBME/vignette numerical quotas are NOT applied to conceptual family-medicine
or environmental-medicine lessons. For decision-labelled MCQs the author must
provide a real counterfactual answer-switch test with source-anchored evidence.
The probe checks that the counterfactual is well formed, NOT that its medical
logic is true. A distinct reviewer remains required for release.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

VERSION = '1.0'
CONCEPTUAL = {'conceptual_principles', 'foundations', 'definitions', 'systems', 'public_health_principles'}
DECISION = {'clinical_decision', 'differential', 'prioritize', 'management', 'interpretation', 'population_reasoning'}
VALID_KEYS = {'A', 'B', 'C', 'D'}


def _norm(value: Any) -> str:
    return re.sub(r'\s+', ' ', str(value)).strip().casefold()


def _error(code: str, item_id: Any, message: str) -> dict:
    return {'code': code, 'item_id': str(item_id), 'message': message}


def audit_lesson_items(questions: list[dict], *, context: Mapping[str, Any],
                       sources: Mapping[str, str], strict: bool = True) -> dict:
    """Return item-level evidence report. If strict, invalid critical-item probes block.

    source values are actual full text (not URLs, UUIDs, or unverified hashes).
    A source quote must occur in the matching full text to be counted.
    """
    errs: list[dict] = []
    notes: list[dict] = []
    if not isinstance(context, Mapping):
        return {'status': 'BLOCKED', 'errors': [_error('CONTEXT_MISSING', '*', 'Need real context')],
                'semantic_validated': False, 'release_allowed': False}
    if not isinstance(questions, list) or not questions:
        return {'status': 'BLOCKED', 'errors': [_error('QUESTIONS_MISSING', '*', 'No questions')],
                'semantic_validated': False, 'release_allowed': False}
    domain = context.get('domain')
    lesson = context.get('lesson_type')
    if domain not in {'surgery', 'family_medicine', 'environmental_medicine', 'occupational_medicine',
                      'internal_medicine', 'public_health', 'other'} or not isinstance(lesson, str) or not lesson.strip():
        errs.append(_error('BAD_LESSON_CONTEXT', '*', 'Explicit subject and lesson type required'))
    if not isinstance(sources, Mapping) or not sources:
        errs.append(_error('FULL_SOURCE_REQUIRED', '*', 'Source text must be loaded, not just source IDs'))
        sources = {}
    conceptual = lesson in CONCEPTUAL
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            errs.append(_error('BAD_ITEM', idx + 1, 'Not an object')); continue
        qid = q.get('id', idx + 1)
        task = q.get('competency')
        if task not in {'recall', 'recognition', 'mechanism', 'communication', 'continuity', 'coordination',
                        'clinical_decision', 'differential', 'prioritize', 'management', 'interpretation',
                        'population_reasoning', 'evidence_appraisal', 'integration'}:
            errs.append(_error('COMPETENCY_NOT_DECLARED', qid, 'Specify what the item evaluates'))
            continue
        if q.get('critical', False) not in {True, False}:
            errs.append(_error('BAD_CRITICAL_FLAG', qid, 'Must be bool'))
        anch = q.get('source_anchor')
        if not isinstance(anch, dict) or not all(isinstance(anch.get(k), str) and anch.get(k) for k in ('source_id', 'exact_quote')):
            errs.append(_error('MISSING_SOURCE_ANCHOR', qid, 'Must anchor claim to an actual source quote'))
        elif anch['source_id'] not in sources or _norm(anch['exact_quote']) not in _norm(sources.get(anch['source_id'], '')):
            errs.append(_error('SOURCE_QUOTE_NOT_FOUND', qid, 'Claim quote absent from source full text'))
        if task in DECISION and bool(q.get('critical', False)):
            probe = q.get('counterfactual_probe')
            if not isinstance(probe, dict):
                errs.append(_error('COUNTERFACTUAL_REQUIRED', qid, 'Critical decision item requires an answer-switch probe'))
                continue
            quote = _norm(probe.get('decisive_quote', ''))
            stem = _norm(q.get('question', ''))
            other = _norm(probe.get('altered_stem', ''))
            orig_key = str(q.get('correct', '')).upper()
            other_key = str(probe.get('altered_correct', '')).upper()
            if len(quote) < 8 or quote not in stem:
                errs.append(_error('DECISIVE_QUOTE_NOT_IN_STEM', qid, 'Quote must occur in actual item'))
            if not other or other == stem or quote in other:
                errs.append(_error('COUNTERFACTUAL_NOT_CHANGED', qid, 'Altered stem must remove/change the decisive finding'))
            if orig_key not in VALID_KEYS or other_key not in VALID_KEYS or orig_key == other_key:
                errs.append(_error('COUNTERFACTUAL_KEY_NOT_SWITCHED', qid, 'Same options must yield a different proposed key'))
            if len(_norm(probe.get('why_switches', ''))) < 35:
                errs.append(_error('COUNTERFACTUAL_RATIONALE_MISSING', qid, 'Must explain the causal pivot'))
        elif task in DECISION and not q.get('critical', False):
            notes.append(_error('OPTIONAL_COUNTERFACTUAL', qid, 'Noncritical decision still needs semantic item review'))
        elif conceptual:
            notes.append(_error('CONCEPTUAL_ITEM_ALLOWED', qid, 'Direct conceptual items are valid if the learning objective warrants them'))
        else:
            notes.append(_error('FOUNDATION_ITEM_ALLOWED', qid, 'Recall is allowed when aligned with the declared objective'))
    return {
        'version': VERSION, 'status': 'BLOCKED' if (strict and errs) else ('STRUCTURE_WARN' if errs else 'STRUCTURE_PASS_REVIEW_REQUIRED'),
        'domain': domain, 'lesson_type': lesson, 'questions': len(questions),
        'source_digests': {k: hashlib.sha256(v.encode('utf-8')).hexdigest() for k, v in sources.items() if isinstance(v, str)},
        'errors': errs, 'notes': notes,
        'semantic_validated': False, 'release_allowed': False,
    }
