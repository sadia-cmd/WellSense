"""The WellSense inference engine.

* Working memory holds (fact, value) pairs, each with a certainty factor (CF) in [-1, 1].
* Forward chaining: an agenda of matching rules; conflict resolution picks one rule per cycle;
  each rule fires at most once (refractoriness). Repeats until nothing new can fire.
* Certainty factors follow MYCIN (Shortliffe & Buchanan, 1975):
    premise CF  = min(CF of the conditions)               (AND)
    conclusion  = rule CF × premise CF
    combining   = CF1 + CF2(1 − CF1) for two positives, etc. (see combine_cf)
* Data quality: a sensor fact enters working memory with CF = the reading's trust
  (1.0 good, 0.8 filled-in, 0.2 frozen), so unreliable evidence counts for little.
* Backward chaining (consult): pick the leading hypothesis, find rules that could confirm or
  reject it using a question only a person can answer, ask it, and chain forward again.
"""
from dataclasses import dataclass, field

DATA_KINDS = ('level', 'trend', 'osc', 'step', 'cycle', 'jump30', 'drift')


def combine_cf(a, b):
    """Combine two certainty factors for the same conclusion (MYCIN)."""
    if a >= 0 and b >= 0:
        return a + b * (1 - a)
    if a < 0 and b < 0:
        return a + b * (1 + a)
    return (a + b) / (1 - min(abs(a), abs(b)))


@dataclass
class Firing:
    cycle: int
    rule_id: str
    premise: list          # [(fact, value, cf)] that matched
    cf_in: float           # premise CF
    contribution: float    # rule CF × premise CF
    result: float          # CF of the conclusion after combining
    agenda_size: int       # how many rules competed in this cycle (conflict set)


@dataclass
class WorkingMemory:
    facts: dict = field(default_factory=dict)          # (fact, value) -> CF
    support: dict = field(default_factory=dict)        # (fact, value) -> [Firing]
    origin: dict = field(default_factory=dict)         # (fact, value) -> 'sensor' / 'user'
    present: set = field(default_factory=set)          # fact names with any value
    fired: set = field(default_factory=set)            # refractoriness
    trace: list = field(default_factory=list)
    asked: dict = field(default_factory=dict)          # question id -> (answer, why text)

    def cf(self, fact, value):
        return self.facts.get((fact, value), 0.0)

    def assert_fact(self, fact, value, cf, origin='sensor'):
        self.facts[(fact, value)] = cf
        self.origin[(fact, value)] = origin
        self.present.add(fact)

    def values(self, fact):
        return {v: c for (f, v), c in self.facts.items() if f == fact}


class InferenceEngine:
    def __init__(self, kb, use_quality=True, keep_trace=True, disabled_rules=()):
        self.kb = kb
        self.use_quality = use_quality
        self.keep_trace = keep_trace
        self.threshold = kb.settings['fact_belief_threshold']
        disabled = set(disabled_rules)
        self.rules = [r for r in kb.rules if r.id not in disabled]

    # ------------------------------------------------------------------ working memory
    def initial_memory(self, row, variables):
        """Build working memory from one row of the ETL 'facts' table (a dict)."""
        wm = WorkingMemory()
        for v in variables:
            rel = row.get(f'{v}_rel')
            rel = 0.0 if rel is None or rel != rel else float(rel)
            q = row.get(f'{v}_q')
            if q is not None:
                wm.assert_fact(f'{v}.quality', q, 1.0)
            trust = rel if self.use_quality else (1.0 if rel > 0 else 0.0)
            if trust <= 0:
                continue                                  # missing/invalid → unknown (incomplete information)
            for k in DATA_KINDS:
                val = row.get(f'{v}_{k}')
                if val is not None and val == val and val != 'UNKNOWN':
                    wm.assert_fact(f'{v}.{k}', val, trust)
        # how many key sensors are trustworthy right now (incomplete-information check)
        key = self.kb.settings.get('key_sensors', [])
        good = sum(1 for v in key if (row.get(f'{v}_rel') or 0) >= 0.5)
        wm.assert_fact('DATA_COVERAGE', 'LOW' if good < self.kb.settings.get('min_key_sensors', 2) else 'OK', 1.0)
        for key in ('dhsv_state', 'gas_lift', 'aber_ckp_trend', 'aber_ckgl_trend', 'well_state'):
            val = row.get(key)
            if val is not None and val == val and val != 'UNKNOWN':
                wm.assert_fact(key.replace('_trend', '.trend'), val, 1.0)
        return wm

    # ------------------------------------------------------------------ matching
    def match(self, rule, wm):
        """Return (premise CF, matched facts) if the rule's conditions hold, else None."""
        if not rule.required <= wm.present:
            return None
        cfs, used = [], []
        for c in rule.conditions:
            best_v, best = None, 0.0
            for v in c.values:
                x = wm.facts.get((c.fact, v), 0.0)
                if x > best:
                    best_v, best = v, x
            believed = best >= self.threshold
            if c.negated:
                if believed:
                    return None
            else:
                if not believed:
                    return None
                cfs.append(best)
                used.append((c.fact, best_v, round(best, 3)))
        return (min(cfs) if cfs else 1.0), used

    # ------------------------------------------------------------------ forward chaining
    def forward_chain(self, wm, max_cycles=500):
        cycle = len(wm.trace)
        while cycle < max_cycles:
            agenda = []
            for r in self.rules:
                if r.id in wm.fired:
                    continue
                m = self.match(r, wm)
                if m:
                    agenda.append((r, m))
            if not agenda:
                break
            # Conflict resolution: 1) salience  2) specificity (more conditions)  3) stronger rule CF
            r, (cf_in, used) = max(agenda, key=lambda a: (a[0].salience, len(a[0].conditions), abs(a[0].cf)))
            wm.fired.add(r.id)
            contribution = r.cf * cf_in
            key = (r.fact, r.value)
            old = wm.facts.get(key)
            new = contribution if old is None else combine_cf(old, contribution)
            wm.facts[key] = new
            wm.origin.setdefault(key, 'inferred')
            wm.present.add(r.fact)
            f = Firing(cycle, r.id, used, round(cf_in, 3), round(contribution, 3), round(new, 3), len(agenda))
            wm.support.setdefault(key, []).append(f)
            if self.keep_trace:
                wm.trace.append(f)
            cycle += 1
        return wm

    # ------------------------------------------------------------------ results
    def diagnoses(self, wm):
        """Fault hypotheses sorted by CF (only those with positive belief)."""
        d = {v: c for (f, v), c in wm.facts.items() if f == 'FAULT' and c > 0}
        return sorted(d.items(), key=lambda x: -x[1])

    def verdict(self, wm):
        """Final answer for one moment: the top fault, NORMAL, or UNDETERMINED (insufficient data)."""
        d = self.diagnoses(wm)
        if d and d[0][1] >= self.kb.settings['alarm_threshold']:
            return d[0]
        if wm.cf('STATUS', 'INSUFFICIENT_DATA') > 0:
            return ('UNDETERMINED', 0.0)
        return ('NORMAL', 0.0)

    def diagnose(self, row, variables):
        wm = self.forward_chain(self.initial_memory(row, variables))
        return wm, self.diagnoses(wm)

    # ------------------------------------------------------------------ backward chaining
    def next_question(self, wm):
        """Goal-driven step: choose the question that can best confirm or reject the leading hypothesis."""
        s = self.kb.settings
        hyps = [(f, c) for f, c in self.diagnoses(wm) if c >= s['ask_threshold']]
        if not hyps or hyps[0][1] >= s['confirm_threshold']:
            return None
        for goal, goal_cf in hyps:
            best = None
            for r in self.kb.by_conclusion.get(('FAULT', goal), []):
                if r.level != 'answer' or r.id in wm.fired:
                    continue
                for c in r.conditions:
                    if c.fact in self.kb.questions and c.fact not in wm.asked:
                        if best is None or abs(r.cf) > abs(best[1].cf):
                            best = (c.fact, r)
            if best:
                qid, _ = best
                effects = []
                for r2 in self.kb.by_conclusion.get(('FAULT', goal), []):
                    for c in r2.conditions:
                        if c.fact == qid:
                            effects.append(f"{c.values[0]} {'raises' if r2.cf > 0 else 'lowers'} it ({r2.id}: {r2.explanation})")
                why = (f"I suspect '{self.kb.faults[goal]['label']}' (CF {goal_cf:.2f}) but cannot confirm it from the sensors. "
                       f"Answer " + '; answer '.join(effects))
                return qid, goal, why
        return None

    def consult(self, wm, ask, max_questions=4):
        """Interactive diagnosis: forward chain, then ask questions (backward chaining) until confident."""
        self.forward_chain(wm)
        for _ in range(max_questions):
            nq = self.next_question(wm)
            if nq is None:
                break
            qid, goal, why = nq
            answer = ask(self.kb.questions[qid], why)
            wm.asked[qid] = (answer, why)
            if answer in self.kb.questions[qid]['answers']:
                wm.assert_fact(qid, answer, 1.0, origin='user')
            self.forward_chain(wm)
        return wm
