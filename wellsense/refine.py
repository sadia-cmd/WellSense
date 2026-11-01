"""Knowledge refinement: check each diagnosis rule against labelled development cases and adjust its CF.

A knowledge engineer normally tests rules on known cases and adjusts certainty factors. Here this is
done systematically:
    precision(rule) = how often the rule's fault is the true situation when the rule fires
                      (averaged per instance, so long instances do not dominate)
    refined CF      = (1 − w) × expert CF + w × precision          (w = 0.5 by default)
Rules with too little evidence (fired in < min_instances instances) keep the expert CF.
Only the development instances are used; the held-out instances are never looked at here.
"""
import json
import os

import numpy as np
import pandas as pd

from .monitor import replay


def truth_per_minute(timeline, event_name):
    phase = timeline['phase']
    return np.where(phase.isin(['transient', 'steady']), event_name,
                    np.where(phase == 'normal', 'NORMAL', None))


def rule_statistics(engine, facts, instances, step=1):
    """Fire the engine on every development minute and record, for each diagnosis rule, whether it was right."""
    kb = engine.kb
    diag = {r.id: r.value for r in kb.rules if r.level == 'diagnosis' and r.cf > 0}
    per_inst = []
    for iid, g in facts.groupby('instance_id'):
        meta = instances.loc[iid]
        if not meta['labels_consistent']:
            continue
        fired = []
        tl = replay(engine, g.reset_index(drop=True), step=step, fired_log=fired)
        truth = truth_per_minute(tl, meta['event_name'])
        for rid, fault in diag.items():
            hits = [truth[i] for i, fl in enumerate(fired) if rid in fl and truth[i] is not None]
            if hits:
                per_inst.append({'rule': rid, 'fault': fault, 'instance_id': iid,
                                 'minutes': len(hits), 'precision': float(np.mean([h == fault for h in hits]))})
    d = pd.DataFrame(per_inst)
    stats = (d.groupby(['rule', 'fault'])
              .agg(instances=('instance_id', 'nunique'), minutes=('minutes', 'sum'), precision=('precision', 'mean'))
              .reset_index())
    expert = {r.id: r.cf for r in kb.rules}
    stats['expert_cf'] = stats['rule'].map(expert)
    return stats


def refine(kb_folder, stats, weight=0.5, min_instances=3, out_name='rules_refined.json'):
    """Write a refined copy of rules.json and return the table of changes."""
    with open(os.path.join(kb_folder, 'rules.json'), encoding='utf-8') as f:
        rules = json.load(f)
    s = stats.set_index('rule')
    changes = []
    for r in rules:
        if r['id'] not in s.index:
            continue
        row = s.loc[r['id']]
        old = r['then']['cf']
        if row['instances'] >= min_instances:
            new = round((1 - weight) * old + weight * row['precision'], 2)
            note = 'refined'
        else:
            new, note = old, 'kept (too few cases)'
        r['then']['cf'] = new
        r['refinement'] = {'expert_cf': old, 'precision': round(float(row['precision']), 3),
                           'instances': int(row['instances']), 'note': note}
        changes.append({'rule': r['id'], 'fault': r['then']['value'], 'instances': int(row['instances']),
                        'precision': round(float(row['precision']), 2), 'expert_cf': old, 'refined_cf': new, 'note': note})
    with open(os.path.join(kb_folder, out_name), 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    return pd.DataFrame(changes).sort_values(['fault', 'rule'])
