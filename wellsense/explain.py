"""Explanation facility: HOW, WHY, WHY-NOT and WHAT-IF."""
import copy


def how(engine, wm, fact, value, depth=0, max_depth=6, seen=None):
    """HOW was (fact, value) concluded? Returns indented text lines tracing the rule chain down to sensor facts."""
    kb = engine.kb
    seen = set() if seen is None else seen
    pad = '    ' * depth
    cf = wm.cf(fact, value)
    lines = []
    origin = wm.origin.get((fact, value))
    if origin == 'sensor':
        q = fact.split('.')[0]
        quality = [v for (f, v), c in wm.facts.items() if f == f'{q}.quality']
        qtxt = f", reading quality {quality[0]}" if quality else ''
        return [f"{pad}• sensor fact {fact} = {value} (trust {cf:.2f}{qtxt})"]
    if origin == 'user':
        return [f"{pad}• operator answered {fact} = {value}"]
    label = kb.faults[value]['label'] if fact == 'FAULT' and value in kb.faults else f'{fact} = {value}'
    lines.append(f"{pad}{label}: CF {cf:+.2f}")
    if (fact, value) in seen or depth >= max_depth:
        return lines
    seen.add((fact, value))
    for f in wm.support.get((fact, value), []):
        r = kb.rule_by_id[f.rule_id]
        lines.append(f"{pad}  ← rule {r.id} \"{r.name}\" (rule CF {r.cf:+.2f} × premise {f.cf_in:.2f} = {f.contribution:+.2f})")
        lines.append(f"{pad}     because: {r.explanation}")
        for (pf, pv, _) in f.premise:
            lines += how(engine, wm, pf, pv, depth + 2, max_depth, seen)
    return lines


def why_not(engine, wm, fault):
    """WHY NOT fault? For every rule that could conclude it, show which conditions failed."""
    kb, thr = engine.kb, engine.threshold
    lines = [f"Why not '{kb.faults[fault]['label']}'?  (current CF {wm.cf('FAULT', fault):+.2f})"]
    for r in kb.by_conclusion.get(('FAULT', fault), []):
        if r.level not in ('diagnosis',) or r.cf <= 0:
            continue
        failed = []
        for c in r.conditions:
            best = max((wm.cf(c.fact, v) for v in c.values), default=0.0)
            if c.negated and best >= thr:
                failed.append(f"{c.fact} IS {'/'.join(c.values)} (CF {best:.2f}) but the rule needs it NOT to be")
            elif not c.negated and best < thr:
                have = {v: round(x, 2) for v, x in wm.values(c.fact).items() if x > 0}
                failed.append(f"needs {c.fact} = {'/'.join(c.values)}; have {have or 'nothing (unknown)'}")
        status = 'FIRED' if r.id in wm.fired else 'did not fire'
        lines.append(f"  {r.id} [{status}] {r.name}")
        for f in failed:
            lines.append(f"      ✗ {f}")
    return lines


def what_if(engine, row, variables, changes):
    """WHAT IF some facts were different? Re-run the diagnosis with changed inputs and compare."""
    before = dict(engine.diagnoses(engine.forward_chain(engine.initial_memory(row, variables))))
    row2 = copy.copy(row)
    row2.update(changes)
    after = dict(engine.diagnoses(engine.forward_chain(engine.initial_memory(row2, variables))))
    faults = sorted(set(before) | set(after), key=lambda f: -max(before.get(f, 0), after.get(f, 0)))
    return [(engine.kb.faults[f]['label'], round(before.get(f, 0), 2), round(after.get(f, 0), 2)) for f in faults]
