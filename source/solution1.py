import csv
import re

def parse_facts(facts_str: str) -> dict:
    """
    Parses a string of facts and extracts key-value pairs.
    Handles numerical and boolean facts.
    """
    facts = {}
    items = facts_str.strip().split(';')
    for item in items:
        item = item.strip()
        if not item:
            continue
        # Case for numerical facts, e.g., 'Frog has $100' or 'Camel has 11 friends'
        match_num = re.search(r'(\w+)\s+has\s+\$(\d+)', item, re.IGNORECASE)
        match_num_friends = re.search(r'(\w+)\s+has\s+(\d+)\s+friends', item, re.IGNORECASE)
        
        if match_num:
            entity, value = match_num.groups()
            facts[entity.lower()] = int(value)
        elif match_num_friends:
            entity, value = match_num_friends.groups()
            facts[f'{entity.lower()}_friends'] = int(value)
        # Case for simple boolean facts, e.g., 'frog attacks cat' or 'cat guards fields'
        else:
            facts[item.lower()] = True
    return facts

def parse_rules(rules_str: str) -> dict:
    """
    Parses a string of rules and extracts their conditions and conclusions.
    """
    rules = {}
    rule_items = rules_str.strip().split(';')
    for item in rule_items:
        item = item.strip()
        if not item:
            continue
        match = re.match(r'(R\d+):\s+if\s+(.+)\s+then\s+(.+)', item, re.IGNORECASE)
        if match:
            rule_id, condition, conclusion = match.groups()
            rules[rule_id] = {'condition': condition.strip(), 'conclusion': conclusion.strip()}
    return rules

def evaluate_condition(condition: str, facts: dict) -> bool:
    """
    Evaluates a rule condition against a dictionary of facts.
    Handles basic logical and arithmetic operations.
    """
    try:
        # Simple boolean check, e.g., 'frog attacks cat'
        if condition.lower() in facts:
            return facts[condition.lower()]
        
        # Handle numerical comparisons, e.g., '>10 friends'
        if condition.startswith('>'):
            val = int(condition.replace('>', ''))
            return any(v > val for k, v in facts.items() if '_friends' in k)

        # Handle arithmetic comparisons, e.g., 'frog > (dog+lion)'
        for entity in ['frog', 'dog', 'lion', 'camel', 'seal']:
            if entity in facts:
                condition = condition.replace(entity, str(facts[entity]))
        
        # Evaluate the expression
        return eval(condition)

    except (NameError, TypeError, SyntaxError):
        # If an entity is not in facts or evaluation fails, the condition is not met.
        return False

def resolve_conflict(activated_rules: dict, preferences: str, question: str) -> str:
    """
    Resolves a conflict based on the provided preference order.
    """
    preferences_order = [p.strip() for p in preferences.split('>')]
    
    for rule_id in preferences_order:
        if rule_id in activated_rules:
            final_conclusion = activated_rules[rule_id]['conclusion']
            
            # Check if the winning conclusion is about the question
            q_entity = re.search(r'Does\s+([\w\s]+)\?', question, re.IGNORECASE)
            if q_entity:
                question_subject = q_entity.group(1).strip().lower()
                if question_subject in final_conclusion.lower():
                    if 'does not' in final_conclusion.lower():
                        return "Disproved"
                    else:
                        return "Proved"
    
    return "Unknown"

def predict_row(facts: str, rules: str, preferences: str, question: str) -> str:
    """
    Main prediction function for a single row.
    """
    facts_parsed = parse_facts(facts)
    rules_parsed = parse_rules(rules)
    
    activated_rules = {}
    for rule_id, rule_content in rules_parsed.items():
        if evaluate_condition(rule_content['condition'], facts_parsed):
            activated_rules[rule_id] = rule_content

    if not activated_rules:
        # No rule is activated, so the conclusion is unknown
        return "Unknown"
    
    # Check for conflicts
    conclusions = {rule['conclusion'] for rule in activated_rules.values()}
    if len(conclusions) == 1 or not preferences:
        # No conflict or no preferences to resolve it.
        conclusion = list(conclusions)
        if 'does not' in conclusion:
            return "Disproved"
        return "Proved"
    else:
        # Resolve conflict using preferences
        return resolve_conflict(activated_rules, preferences, question)

def eval_csv(path: str) -> float:
    """
    Evaluates the accuracy of the predictions from a CSV file.
    (Provided by the user)
    """
    total, correct = 0, 0
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            pred = predict_row(row['facts'], row['rules'], row['preferences'], row['question'])
            ok = (pred == row['label'])
            total += 1
            correct += int(ok)
            print(f"id:{row['id']} predicted: {pred} ({'correct' if ok else 'wrong'})")
    acc = correct / max(1, total)
    print(f"Overall Accuracy: {acc:.2f}")
    return acc

if __name__ == '__main__':
    # Call the main evaluation function with the path to the CSV file
    eval_csv('defeasible_tasks.csv')