"""Loading and checking the WellSense knowledge base (the JSON files in knowledge_base/)."""
import json
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Condition:
    fact: str
    values: tuple          # the condition holds if the fact has ANY of these values
    negated: bool = False  # negation-as-failure: holds when the fact is NOT believed

    def __str__(self):
        v = self.values[0] if len(self.values) == 1 else '/'.join(self.values)
        return f"NOT {self.fact} = {v}" if self.negated else f"{self.fact} = {v}"


@dataclass
class Rule:
    id: str
    name: str
    level: str
    salience: int
    conditions: list
    fact: str              # conclusion fact
    value: str             # conclusion value
    cf: float              # rule certainty factor (negative = evidence against)
    sources: list
    explanation: str
    required: frozenset = field(default=frozenset())   # facts that must be present for the rule to match

    def __str__(self):
        ifs = ' AND '.join(str(c) for c in self.conditions)
        return f"{self.id}: IF {ifs} THEN {self.fact} = {self.value} (CF {self.cf:+.2f})"


class KnowledgeBase:
    def __init__(self, folder='knowledge_base', rules_file='rules.json'):
        def load(name):
            with open(os.path.join(folder, name), encoding='utf-8') as f:
                return json.load(f)
        self.folder = folder
        self.ontology = load('ontology.json')
        self.sources = {s['id']: s for s in load('sources.json')}
        self.questions = {q['id']: q for q in load('questions.json')}
        self.actions = load('actions.json')
        self.constraints = {c['id']: c for c in load('constraints.json')}
        self.profiles = load('profiles.json')
        self.settings = load('settings.json')
        self.faults = self.ontology['faults']
        self.rules = []
        self.rules_file = rules_file
        for r in load(rules_file):
            conds = [Condition(c['fact'], tuple(c['in']) if 'in' in c else (c['is'],), bool(c.get('not')))
                     for c in r['if']]
            req = frozenset(c.fact for c in conds if not c.negated)
            self.rules.append(Rule(r['id'], r['name'], r['level'], r['salience'], conds, r['then']['fact'],
                                   r['then']['value'], r['then']['cf'], r['sources'], r['explanation'], req))
        self.rule_by_id = {r.id: r for r in self.rules}
        self.by_conclusion = {}
        for r in self.rules:
            self.by_conclusion.setdefault((r.fact, r.value), []).append(r)

    def validate(self, data_facts=()):
        """Return a list of problems found in the knowledge base (empty list = consistent)."""
        problems = []
        ids = [r.id for r in self.rules]
        if len(ids) != len(set(ids)):
            problems.append('duplicate rule ids')
        concluded = {r.fact for r in self.rules}
        known = set(data_facts) | concluded | set(self.questions)
        for r in self.rules:
            for c in r.conditions:
                if data_facts and c.fact not in known:
                    problems.append(f'{r.id}: condition uses unknown fact {c.fact}')
            for s in r.sources:
                if s not in self.sources:
                    problems.append(f'{r.id}: unknown source {s}')
            if not -1 <= r.cf <= 1:
                problems.append(f'{r.id}: CF outside [-1, 1]')
        for f in self.faults:
            if not any(r.value == f and r.cf > 0 and r.level == 'diagnosis' for r in self.rules):
                problems.append(f'{f}: no diagnosis rule')
            if not any(a['fault'] == f and not a['violates'] for a in self.actions):
                problems.append(f'{f}: no safe action')
            if not any(f in q['about'] for q in self.questions.values()):
                problems.append(f'{f}: no question for backward chaining')
        for a in self.actions:
            if a['violates'] and a['violates'] not in self.constraints:
                problems.append(f"{a['id']}: unknown constraint {a['violates']}")
        return problems
