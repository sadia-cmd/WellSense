"""Evaluation helpers: run the KBS over many instances and score the results."""
import sqlite3
import time

import numpy as np
import pandas as pd

from .monitor import replay, alarms, summarise_instance


def load_instance(con, iid):
    return pd.read_sql('SELECT * FROM facts WHERE instance_id = ? ORDER BY timestamp', con, params=(iid,))


def run(engine, db_path, instance_ids, instances, progress_every=100, transform=None, step=1):
    """Replay every instance and summarise it. `transform(df)` can modify the facts first (robustness tests)."""
    kb = engine.kb
    faults = list(kb.faults)
    s = kb.settings
    out, t0 = [], time.time()
    con = sqlite3.connect(db_path)
    for k, iid in enumerate(instance_ids):
        g = load_instance(con, iid)
        if transform is not None:
            g = transform(g)
        tl = replay(engine, g, step=step)
        al = alarms(tl, faults, s['alarm_threshold'], s['alarm_persistence_min'], step=step)
        meta = instances.loc[iid]
        on = meta['onset_minute']
        r = summarise_instance(tl, al, None if pd.isna(on) else on, faults)
        r.update(instance_id=iid, well_id=meta['well_id'], true=meta['event_name'],
                 labels_consistent=bool(meta['labels_consistent']), minutes=len(g))
        out.append(r)
        if progress_every and (k + 1) % progress_every == 0:
            print(f'  {k + 1}/{len(instance_ids)} instances  ({time.time() - t0:.0f}s)')
    con.close()
    res = pd.DataFrame(out)
    res['correct'] = res['true'] == res['predicted']
    return res


def scores(res):
    """Headline numbers over label-consistent instances."""
    r = res[res['labels_consistent']]
    per_class = r.groupby('true')['correct'].mean()
    normal = r[r['true'] == 'NORMAL']
    events = r[r['true'] != 'NORMAL']
    return pd.Series({
        'instances': len(r),
        'accuracy': r['correct'].mean(),
        'balanced_accuracy': per_class.mean(),
        'event_detection_rate': (~events['predicted'].isin(['NORMAL', 'UNDETERMINED'])).mean(),
        'false_alarm_rate_normal_wells': (~normal['predicted'].isin(['NORMAL', 'UNDETERMINED'])).mean() if len(normal) else np.nan,
        'alarm_during_labelled_normal_minutes': r['alarm_before_onset'].mean(),
        'undetermined_rate': (r['predicted'] == 'UNDETERMINED').mean(),
        'median_detection_delay_min': events['detection_delay_min'].median(),
    })


def per_class(res):
    r = res[res['labels_consistent']]
    t = r.groupby('true').agg(instances=('correct', 'size'), recall=('correct', 'mean'),
                              detected_as_some_fault=('predicted', lambda p: (~p.isin(['NORMAL', 'UNDETERMINED'])).mean()),
                              median_delay_min=('detection_delay_min', 'median'))
    pred_counts = r['predicted'].value_counts()
    t['precision'] = [((r['predicted'] == c) & r['correct']).sum() / pred_counts.get(c, np.nan) for c in t.index]
    return t[['instances', 'recall', 'precision', 'detected_as_some_fault', 'median_delay_min']]
