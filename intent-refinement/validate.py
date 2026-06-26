#!/usr/bin/env python3
"""Validator for Narrative-Driven Development (NDD) specifications."""

import sys
import os

try:
    import yaml
except ImportError:
    print("Error: 'pyyaml' is required to parse YAML files.")
    print("Please install it using: pip install pyyaml")
    print("Or convert your specification to JSON and use a JSON validator.")
    sys.exit(1)

VALID_MOMENT_TYPES = {"Command", "Query", "React", "Experience"}

def validate_spec(data):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        errors.append("Root of the document must be a dictionary.")
        return errors, warnings

    # 1. Domain Validation
    if "domain" not in data:
        errors.append("Missing 'domain' key at root.")
    elif not isinstance(data["domain"], str):
        errors.append("'domain' must be a string.")

    if "description" not in data:
        warnings.append("Missing 'description' at root.")

    # 2. Narratives Validation
    if "narratives" not in data:
        errors.append("Missing 'narratives' key at root.")
        return errors, warnings

    narratives = data["narratives"]
    if not isinstance(narratives, list):
        errors.append("'narratives' must be a list.")
        return errors, warnings

    for i, narrative in enumerate(narratives):
        path = f"narratives[{i}]"
        if not isinstance(narrative, dict):
            errors.append(f"{path} must be a dictionary.")
            continue

        n_name = narrative.get("name", "unnamed")
        if "name" not in narrative:
            errors.append(f"Missing 'name' in {path}.")
        if "goal" not in narrative:
            warnings.append(f"Missing 'goal' in {path} ({n_name}).")

        # For cohesion checks
        commands = []
        queries = []

        # 3. Scenes Validation
        if "scenes" not in narrative:
            errors.append(f"Missing 'scenes' in {path} ({n_name}).")
            continue

        scenes = narrative["scenes"]
        if not isinstance(scenes, list):
            errors.append(f"'scenes' in {path} must be a list.")
            continue

        for j, scene in enumerate(scenes):
            scene_path = f"{path}.scenes[{j}]"
            if not isinstance(scene, dict):
                errors.append(f"{scene_path} must be a dictionary.")
                continue

            s_name = scene.get("name", "unnamed")
            if "name" not in scene:
                errors.append(f"Missing 'name' in {scene_path}.")
            if "outcome" not in scene:
                warnings.append(f"Missing 'outcome' in {scene_path} ({s_name}).")

            # 4. Moments Validation
            if "moments" not in scene:
                errors.append(f"Missing 'moments' in {scene_path} ({s_name}).")
                continue

            moments = scene["moments"]
            if not isinstance(moments, list):
                errors.append(f"'moments' in {scene_path} must be a list.")
                continue

            for k, moment in enumerate(moments):
                moment_path = f"{scene_path}.moments[{k}]"
                if not isinstance(moment, dict):
                    errors.append(f"{moment_path} must be a dictionary.")
                    continue

                m_name = moment.get("name", "unnamed")
                m_type = moment.get("type")

                if "name" not in moment:
                    errors.append(f"Missing 'name' in {moment_path}.")

                if "type" not in moment:
                    errors.append(f"Missing 'type' in {moment_path} ({m_name}).")
                elif m_type not in VALID_MOMENT_TYPES:
                    errors.append(f"Invalid type '{m_type}' in {moment_path} ({m_name}). Must be one of {VALID_MOMENT_TYPES}.")
                else:
                    if m_type == "Command":
                        commands.append(m_name)
                    elif m_type == "Query":
                        queries.append(m_name)

                # 5. Rules & Examples Validation
                rules = moment.get("rules", [])
                if not isinstance(rules, list):
                    errors.append(f"'rules' in {moment_path} ({m_name}) must be a list.")
                    continue

                if m_type in {"Command", "React"} and not rules:
                    warnings.append(f"Moment '{m_name}' ({m_type}) has no rules defined. Commands and Reacts usually require rules.")

                for l, rule in enumerate(rules):
                    rule_path = f"{moment_path}.rules[{l}]"
                    if not isinstance(rule, dict):
                        # Allow simple string rules, but warn that examples are preferred
                        if isinstance(rule, str):
                            warnings.append(f"Rule in {moment_path} is a simple string. Consider using structured rule with examples.")
                            continue
                        else:
                            errors.append(f"{rule_path} must be a dictionary or string.")
                            continue

                    if "text" not in rule:
                        errors.append(f"Missing 'text' in {rule_path}.")

                    examples = rule.get("examples", [])
                    if not isinstance(examples, list):
                        errors.append(f"'examples' in {rule_path} must be a list.")
                        continue

                    if not examples:
                        warnings.append(f"Rule '{rule.get('text', 'unnamed')}' in {moment_path} has no examples. Examples are highly recommended.")

                    for m, example in enumerate(examples):
                        ex_path = f"{rule_path}.examples[{m}]"
                        if not isinstance(example, dict):
                            errors.append(f"{ex_path} must be a dictionary.")
                            continue

                        if "name" not in example:
                            errors.append(f"Missing 'name' in {ex_path}.")
                        if "given" not in example:
                            errors.append(f"Missing 'given' in {ex_path} ({example.get('name', 'unnamed')}).")
                        if "when" not in example:
                            errors.append(f"Missing 'when' in {ex_path} ({example.get('name', 'unnamed')}).")
                        if "then" not in example:
                            errors.append(f"Missing 'then' in {ex_path} ({example.get('name', 'unnamed')}).")

        # Cohesion check: Commands without Queries
        if commands and not queries:
            warnings.append(f"Narrative '{n_name}' has Commands {commands} but no Queries. The system state changes, but there is no defined way to read it in this narrative.")
        # Cohesion check: Queries without Commands (might be okay if it's read-only, but worth a warning if it's a main flow)
        elif queries and not commands:
            warnings.append(f"Narrative '{n_name}' has Queries {queries} but no Commands. This narrative is read-only. Ensure this is intentional.")

    return errors, warnings

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate.py <path_to_spec.yaml>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)

    print(f"Validating {file_path}...")
    errors, warnings = validate_spec(data)

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - [WARNING] {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - [ERROR] {error}")
        print(f"\nValidation failed with {len(errors)} errors and {len(warnings)} warnings.")
        sys.exit(1)
    else:
        print("\nValidation successful! Specification is valid NDD.")
        if warnings:
            print(f"Passed with {len(warnings)} warnings.")
        sys.exit(0)

if __name__ == "__main__":
    main()
