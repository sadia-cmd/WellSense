"""Maintenance decision support: rank actions for a diagnosis under a stakeholder profile.

Safety constraints are HARD: an action that violates one is never recommended, whatever the
profile. The remaining actions are ranked by a weighted score of four criteria (multi-criteria
decision making). All criteria are scored 1–5 in actions.json.
"""
import pandas as pd


def score(action, weights):
    s = (weights['safety_risk'] * (5 - action['safety_risk']) / 4 +
         weights['production_loss'] * (5 - action['production_loss']) / 4 +
         weights['cost'] * (5 - action['cost']) / 4 +
         weights['effectiveness'] * (action['effectiveness'] - 1) / 4)
    return round(s, 3)


def recommend(kb, fault, profile='SAFETY_FIRST', sensor_alerts=(), wm=None):
    """Return a table of candidate actions for `fault`, best first.

    Unsafe actions are listed as BLOCKED (hard safety constraint). If the working memory `wm` of the
    diagnosis is given, actions whose 'not_when' condition holds in the current situation are listed as
    NOT APPLICABLE (e.g. inhibitor dosing once a hydrate plug has stopped the flow).
    """
    weights = kb.profiles[profile]['weights']
    rows = []
    targets = [fault] + [f"SENSOR:{a.split('_')[0]}" for a in sensor_alerts]
    for a in kb.actions:
        if a['fault'] not in targets:
            continue
        blocked = a['violates']
        nw = a.get('not_when')
        inapplicable = bool(nw and wm is not None and wm.cf(nw['fact'], nw['is']) >= kb.settings['fact_belief_threshold'])
        rows.append({
            'action': a['text'], 'id': a['id'],
            'for': 'sensor' if a['fault'].startswith('SENSOR') else 'fault',
            'safety_risk': a['safety_risk'], 'production_loss': a['production_loss'],
            'cost': a['cost'], 'effectiveness': a['effectiveness'],
            'score': None if (blocked or inapplicable) else score(a, weights),
            'status': f"BLOCKED by {blocked}" if blocked else ('NOT APPLICABLE now' if inapplicable else 'allowed'),
            'why': (kb.constraints[blocked]['text'] if blocked else (nw['reason'] if inapplicable else a['why'])),
        })
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    t['rank'] = t['score'].rank(ascending=False, method='first')
    t = t.sort_values(['for', 'rank'], ascending=[True, True], na_position='last')
    t['rank'] = t['rank'].astype('Int64')
    return t.reset_index(drop=True)[['rank', 'id', 'action', 'for', 'safety_risk', 'production_loss', 'cost',
                                     'effectiveness', 'score', 'status', 'why']]


def compare_profiles(kb, fault, wm=None):
    """Show how the top recommendation changes between stakeholder profiles."""
    out = []
    for p, spec in kb.profiles.items():
        t = recommend(kb, fault, p, wm=wm)
        t = t[(t['for'] == 'fault') & t['score'].notna()]
        top = t.iloc[0]
        out.append({'profile': spec['label'], 'top action': top['action'], 'score': top['score']})
    return pd.DataFrame(out)
