#!/usr/bin/env python3
# CPU-only, standard library only.
import csv, re, sys
from typing import Dict, Tuple, List, Optional, Set

# ----------------------------
# Normalization helpers
# ----------------------------
AUX_NEG_PAT = re.compile(r"\b(don't|doesn't|didn't|cannot|can't|won't|isn't|aren't|wasn't|weren't|shouldn't|wouldn't|couldn't)\b")
PUNCT_PAT = re.compile(r"[^\w\s\+\-\(\)]")

def normalize_text(s: str) -> str:
    """
    Lowercase, expand common negation contractions into 'not', remove extra punctuation,
    collapse whitespace. Keep + - ( ) for simple expression parsing later.
    """
    s = s.lower().strip()
    # expand common negation contractions to include 'not'
    s = AUX_NEG_PAT.sub("not", s)
    # standardize "does not", "do not", "is not" forms when they appear split
    s = re.sub(r"\b(does|do|is|are|was|were|has|have)\s+not\b", "not", s)
    # remove punctuation except + - ( )
    s = PUNCT_PAT.sub(" ", s)
    # collapse spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_predicate(s: str) -> str:
    """
    Build a light-weight, comparison-friendly predicate string from the question or conclusion.
    Removes leading auxiliaries like 'does', 'do', 'is', 'are', articles, and trailing '?',
    and de-pluralizes a simple trailing 's' on verbs (best-effort).
    """
    s = normalize_text(s)
    # remove question words like 'does', 'do', 'is', etc. at start
    s = re.sub(r"^(does|do|is|are|was|were|can|should|would|could)\s+", "", s)
    # remove leading articles
    s = re.sub(r"^(the|a|an)\s+", "", s)
    # naive de-pluralize verbs like "builds" -> "build"
    s = re.sub(r"\b(\w+?)s\b", r"\1", s)  # crude but helps for 'builds'/'triggers'
    return s.strip()

# --- Helpers to parse numbers like "$100" or "100" ---
def extract_number(s: str) -> int:
    m = re.search(r'(-?\d+)', s)
    return int(m.group(1)) if m else 0

def parse_preferences(pref_str: str) -> Dict[str,int]:
    """
    Parse priorities like: "R2>R1, R3>R2". Higher number => higher priority.
    Returns a dict of rule -> priority (default 0).
    """
    prio: Dict[str,int] = {}
    if not pref_str:
        return prio
    # Assign increasing priority from left to right across each chain
    for chain in re.split(r'[;,]\s*', pref_str.strip()):
        if not chain:
            continue
        parts = [p.strip() for p in re.split(r'\s*>\s*', chain) if p.strip()]
        if not parts:
            continue
        # Rightmost gets lowest, leftmost highest
        for rank, rule in enumerate(parts[::-1]):
            prio[rule] = max(prio.get(rule, 0), rank)
    return prio

def facts_dict(facts: str) -> Dict[int,str]:
    """
    Normalize facts into an index -> text dict, preserving each fact line.
    """
    items = []
    for f in re.split(r';\s*', facts.strip()):
        f = f.strip()
        if f:
            items.append(normalize_text(f))
    return {i: items[i] for i in range(len(items))}

def all_facts_text(fd: Dict[int,str]) -> str:
    return " ; ".join(fd.values())

# --- Numeric aggregation from facts ---
def sum_for_term(fd: Dict[int, str], term: str) -> int:
    """
    Sum numeric values associated with a 'term' across all facts.
    If a fact string contains the 'term' token, any number in that fact contributes.
    """
    term = normalize_text(term)
    total = 0
    for v in fd.values():
        # ensure token-ish presence (avoid partials as much as possible)
        if re.search(rf"\b{re.escape(term)}\b", v):
            m = re.search(r'(-?\d+)', v)
            if m:
                total += int(m.group(1))
    return total

def eval_side_expression(fd: Dict[int, str], expr: str) -> int:
    """
    Evaluate a simple additive expression like: 'frog', 'dog+lion', 'friends', '10', '(dog+lion)'
    We support + between tokens; each token's value is sum_for_term(...) unless it's a pure number.
    Parentheses are ignored (best-effort).
    """
    expr = normalize_text(expr)
    expr = expr.replace("(", "").replace(")", "")
    parts = [p.strip() for p in expr.split('+') if p.strip()]
    total = 0
    for p in parts:
        if re.fullmatch(r'-?\d+', p):
            total += int(p)
        else:
            total += sum_for_term(fd, p)
    return total

def evaluate_condition(fd: Dict[int,str], cond: str) -> bool:
    """
    Evaluate 'cond' against facts. Supports comparators: >, <, >=, <=, =, ==, !=
    Also supports unary thresholds like '> 10 friends' by interpreting the right-most number
    and left-most measure.
    Also supports phrase conditions (substring) when no comparator detected.
    """
    cond = normalize_text(cond)
    if not cond:
        return True  # empty condition => tautology

    # First, comparator-based conditions
    comp_pat = r"(>=|<=|!=|==|=|>|<)"
    m = re.search(comp_pat, cond)
    if m:
        op = m.group(1)
        left = cond[:m.start()].strip()
        right = cond[m.end():].strip()
        # Evaluate both sides as expressions (sum tokens/numbers)
        lv = eval_side_expression(fd, left) if left else 0
        rv = eval_side_expression(fd, right) if right else 0
        if op in (">",):   return lv > rv
        if op in ("<",):   return lv < rv
        if op in (">=",):  return lv >= rv
        if op in ("<=",):  return lv <= rv
        if op in ("=", "=="): return lv == rv
        if op in ("!=",):  return lv != rv
        return False

    # Threshold pattern like '> 10 friends'
    m2 = re.match(r"([><]=?)\s*(-?\d+)\s+(\w+)", cond)
    if m2:
        op, num, measure = m2.group(1), int(m2.group(2)), m2.group(3)
        lv = eval_side_expression(fd, measure)
        rv = num
        if op == ">":  return lv > rv
        if op == "<":  return lv < rv
        if op == ">=": return lv >= rv
        if op == "<=": return lv <= rv

    # Otherwise, treat as phrase existence: all content words must appear in facts
    words = [w for w in cond.split() if w not in {"if", "then", "and", "or"}]
    hay = all_facts_text(fd)
    return all(re.search(rf"\b{re.escape(w)}\b", hay) for w in words)

# ----------------------------
# Rule parsing and application
# ----------------------------
RULE_ID_RE = re.compile(r'^\s*(R\d+):\s*(.*)$', re.I)

def parse_rule(chunk: str) -> Tuple[str, str]:
    """
    Returns (rule_id, rule_body). If no R#: prefix is found, id becomes 'R?'.
    """
    m = RULE_ID_RE.match(chunk)
    if m:
        return m.group(1), m.group(2)
    return "R?", chunk.strip()

def split_if_then(body: str) -> Tuple[str, str]:
    """
    Split 'if ... then ...' into (condition, conclusion).
    If no 'if' found, treat whole body as conclusion with empty condition.
    """
    body_n = normalize_text(body)
    m = re.match(r"if\s+(.+?)\s+then\s+(.+)$", body_n)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Fallback: no explicit if/then => conclusion-only rule
    return "", body_n

def conclusion_is_negative(concl: str) -> bool:
    """
    Determine if conclusion conveys negation (e.g., 'not build', 'does not', 'no X', etc.).
    """
    c = normalize_text(concl)
    # common negation tokens after normalization
    return bool(re.search(r"\bnot\b|\bno\b|\bnever\b", c))

def predicate_match(conclusion: str, target_pred: str) -> bool:
    """
    Heuristic: check if conclusion overlaps with the target predicate (from the question).
    We compare content-word sets with a lenient subset test.
    """
    c = normalize_predicate(conclusion)
    t = normalize_predicate(target_predicate_text(target_pred))
    # Token sets minus stopwords
    stop = {"the","a","an","to","of","in","on","at","by","for"}
    cset = {w for w in c.split() if w not in stop}
    tset = {w for w in t.split() if w not in stop}
    # Match if tset is subset of cset, or vice versa if conclusion is shorter phrasing.
    return bool(tset) and (tset.issubset(cset) or cset.issubset(tset))

def target_predicate_text(question: str) -> str:
    """
    Extract a predicate-like text from the question. E.g.:
    'Does frog build plant?' -> 'frog build plant'
    """
    q = normalize_text(question)
    q = re.sub(r"\?$", "", q)
    q = re.sub(r"^(does|do|is|are|was|were|can|should|would|could)\s+", "", q)
    return q.strip()

def rule_applies(rule: str, fd: Dict[int,str], question: str) -> Tuple[bool, str, Optional[str]]:
    """
    Determine if a rule antecedent holds under the facts.
    Return (applies, effect, derived_fact)
      - applies: True if condition satisfied
      - effect: 'support' or 'block' (only if conclusion matches the question predicate),
                else '' (meaning this rule may still derive a new fact but doesn't directly vote)
      - derived_fact: normalized conclusion to add into facts if applies and effect is '' or 'support'
                      (we don't add blocking conclusions as facts unless needed for chains)
    """
    cond, concl = split_if_then(rule)
    if not evaluate_condition(fd, cond):
        return (False, "", None)

    # If it applies, decide if it directly supports/blocks the question
    eff = ""
    if predicate_match(concl, question):
        eff = "block" if conclusion_is_negative(concl) else "support"

    # We allow chaining by adding positive conclusions (and neutral ones) as derived facts.
    derived = None
    if not conclusion_is_negative(concl):
        # store a succinct normalized conclusion as a fact line
        derived = normalize_text(concl)

    return (True, eff, derived)

def answer_from_effects(effects: List[Tuple[str,int]]) -> str:
    """
    Given list of (effect, priority) where effect in {'support','block'},
    decide Proved / Disproved / Unknown using highest-priority outcome.
    Ties on priority break toward 'block'.
    """
    if not effects:
        return "Unknown"
    best = max(effects, key=lambda x: (x[1], 1 if x[0]=='support' else 2))
    return "Proved" if best[0] == 'support' else "Disproved"

def predict_row(facts: str, rules: str, preferences: str, question: str) -> str:
    fd = facts_dict(facts)
    prio = parse_preferences(preferences)
    effects: List[Tuple[str,int]] = []

    # Split rules into (id, body)
    rule_items: List[Tuple[str,str]] = []
    for chunk in re.split(r';\s*', rules or ""):
        chunk = chunk.strip()
        if not chunk:
            continue
        rid, body = parse_rule(chunk)
        rule_items.append((rid, body))

    # Iterative application to allow simple chaining of derived facts
    seen_derived: Set[str] = set()
    changed = True
    max_passes = 5  # small upper bound for safety
    passes = 0

    while changed and passes < max_passes:
        passes += 1
        changed = False
        for rid, body in rule_items:
            applies, effect, derived = rule_applies(body, fd, question)
            if not applies:
                continue
            # Collect effect if rule conclusion targets the question
            if effect in ("support","block"):
                effects.append((effect, prio.get(rid, 0)))
            # Add derived fact for chaining (only if new)
            if derived and derived not in fd.values() and derived not in seen_derived:
                idx = max(fd.keys()) + 1 if fd else 0
                fd[idx] = derived
                seen_derived.add(derived)
                changed = True

    return answer_from_effects(effects)

def eval_csv(path: str) -> float:
    total, correct = 0, 0
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            pred = predict_row(row['facts'], row['rules'], row['preferences'], row['question'])
            ok = (pred == row['label'])
            total += 1; correct += int(ok)
            print(f"id:{row['id']} predicted: {pred} ({'correct' if ok else 'wrong'})")
    acc = correct / max(1,total)
    print(f"Overall Accuracy: {acc:.2f}")
    return acc

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'defeasible_tasks.csv'
    eval_csv(path)
