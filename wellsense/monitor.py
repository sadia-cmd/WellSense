"""Run the KBS over time (real-time monitoring replay) and turn CFs into alarms."""
import numpy as np
import pandas as pd

ANALOG = ['p_pdg', 't_pdg', 'p_tpt', 't_tpt', 'p_mon_ckp', 't_mon_ckp', 'p_jus_ckp', 't_jus_ckp',
          'p_mon_ckgl', 'p_jus_ckgl', 'p_anular', 'qgl']


def replay(engine, facts_instance, step=1, variables=ANALOG, fired_log=None):
    """Diagnose every `step`-th minute of one instance. Returns one row per evaluated minute with each fault's CF."""
    faults = list(engine.kb.faults)
    recs = []
    rows = facts_instance.to_dict('records')
    for i in range(0, len(rows), step):
        row = rows[i]
        wm = engine.forward_chain(engine.initial_memory(row, variables))
        rec = {'minute': i, 'timestamp': row['timestamp'], 'phase': row.get('phase')}
        for f in faults:
            rec[f] = max(wm.cf('FAULT', f), 0.0)
        rec['insufficient_data'] = wm.cf('STATUS', 'INSUFFICIENT_DATA') > 0
        if fired_log is not None:
            fired_log.append(sorted(r for r in wm.fired if r.startswith('D-')))
        alerts = [v for (fa, v), c in wm.facts.items() if fa == 'SENSOR_ALERT' and c > 0]
        rec['sensor_alerts'] = ','.join(sorted(alerts))
        recs.append(rec)
    return pd.DataFrame(recs)


def alarms(timeline, faults, threshold, persistence_min, step=1):
    """An alarm for a fault is raised when its CF stays ≥ threshold for `persistence_min` minutes in a row."""
    need = max(1, int(np.ceil(persistence_min / step)))
    out = pd.DataFrame(index=timeline.index)
    for f in faults:
        above = (timeline[f] >= threshold).astype(int)
        run = above.groupby((above == 0).cumsum()).cumsum()
        out[f] = run >= need
    return out


def summarise_instance(timeline, alarm_table, onset_minute, faults, min_coverage=0.5, rule='longest'):
    """Instance-level outcome.

    predicted   = the fault with the LONGEST total alarm time (the fault the KBS was most persistently confident about).
                  rule='first' uses the first confirmed alarm instead ("first-out"); it was tested on the development
                  set and rejected (slugging needs 2 h of history, so other alarms came first).
                  NORMAL if no alarm; UNDETERMINED if no alarm and the KBS lacked trustworthy sensors most of the time.
    false alarm = an alarm during minutes Petrobras labelled NORMAL.
    """
    counts = alarm_table[faults].sum()
    first_out = None
    if counts.max() > 0:
        any_al = alarm_table[faults].any(axis=1)
        first_row = alarm_table[faults][any_al].iloc[0]
        first_out = first_row[first_row].index[0]
    if counts.max() > 0 and rule == 'first':
        predicted = first_out
    elif counts.max() > 0:
        predicted = counts.idxmax()
    elif timeline['insufficient_data'].mean() > min_coverage:
        predicted = 'UNDETERMINED'
    else:
        predicted = 'NORMAL'
    any_alarm = alarm_table[faults].any(axis=1)
    first_alarm = int(timeline.loc[any_alarm, 'minute'].iloc[0]) if any_alarm.any() else None
    normal_min = timeline['phase'] == 'normal'
    if onset_minute is not None and not np.isnan(onset_minute):
        pre = timeline['minute'] < onset_minute
        false_alarm_pre_onset = bool(any_alarm[pre & normal_min].any())
        hit = alarm_table.loc[~pre, predicted] if predicted in faults else pd.Series(dtype=bool)
        first_hit = int(timeline.loc[hit[hit].index, 'minute'].iloc[0]) if len(hit) and hit.any() else None
        delay = (first_hit - onset_minute) if first_hit is not None else None
    else:
        false_alarm_pre_onset = bool(any_alarm[normal_min].any())
        delay = None
    return {'predicted': predicted, 'first_alarm_minute': first_alarm, 'detection_delay_min': delay,
            'alarm_before_onset': false_alarm_pre_onset}
