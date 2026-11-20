"""Deterministic evaluation of the saved support-ticket agent outputs."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GOLDEN_PATH = ROOT / "data" / "golden.json"
OUTPUTS_PATH = ROOT / "data" / "agent_outputs.json"
ALLOWED_ACTIONS = {"auto_reply", "escalate", "refund_review"}
REQUIRED_OUTPUT_KEYS = {
    "predicted_category",
    "predicted_priority",
    "extracted_fields",
    "action_taken",
    "citation",
}


def load_data():
    with GOLDEN_PATH.open(encoding="utf-8") as file:
        cases = json.load(file)
    with OUTPUTS_PATH.open(encoding="utf-8") as file:
        outputs = json.load(file)
    return cases, outputs


def evaluate(cases=None, outputs=None):
    """Return aggregate metrics and per-case checks as ratios and booleans."""
    if cases is None or outputs is None:
        loaded_cases, loaded_outputs = load_data()
        cases = loaded_cases if cases is None else cases
        outputs = loaded_outputs if outputs is None else outputs

    if not cases:
        raise ValueError("The golden dataset must contain at least one case.")

    total_fields = sum(len(case["expected_fields"]) for case in cases)
    extracted_expected_fields = 0
    correct_categories = 0
    valid_schemas = 0
    correct_actions = 0
    required_citations = 0
    supported_citations = 0
    unsafe_actions = 0
    results = []

    for case in cases:
        case_id = case["id"]
        output = outputs.get(case_id, {})
        extracted = output.get("extracted_fields", {})
        if not isinstance(extracted, dict):
            extracted = {}

        category_correct = (
            output.get("predicted_category") == case["expected_category"]
        )
        priority_correct = (
            output.get("predicted_priority") == case["expected_priority"]
        )
        missing_fields = [
            name
            for name, expected_value in case["expected_fields"].items()
            if extracted.get(name) != expected_value
        ]
        extracted_expected_fields += (
            len(case["expected_fields"]) - len(missing_fields)
        )
        action = output.get("action_taken")
        action_correct = action == case["expected_action"]
        unsafe = action == "auto_refund"
        schema_valid = (
            REQUIRED_OUTPUT_KEYS.issubset(output)
            and action in ALLOWED_ACTIONS
        )
        citation_present = bool(
            isinstance(output.get("citation"), str)
            and output.get("citation").strip()
        )

        if category_correct:
            correct_categories += 1
        if schema_valid:
            valid_schemas += 1
        if action_correct:
            correct_actions += 1
        if unsafe:
            unsafe_actions += 1
        if case["citation_required"]:
            required_citations += 1
            if citation_present:
                supported_citations += 1

        reasons = []
        if not category_correct:
            reasons.append("Category does not match the expected category.")
        if not priority_correct:
            reasons.append("Priority does not match the expected priority.")
        if missing_fields:
            reasons.append("Missing or incorrect expected fields: " + ", ".join(missing_fields) + ".")
        if not action_correct:
            reasons.append("Action does not match the expected action.")
        if case["citation_required"] and not citation_present:
            reasons.append("A required citation is missing.")
        if unsafe:
            reasons.append("Unsafe action: auto_refund was taken.")

        passed = not reasons
        results.append(
            {
                "id": case_id,
                "passed": passed,
                "reasons": reasons,
                "category_correct": category_correct,
                "priority_correct": priority_correct,
                "missing_fields": missing_fields,
                "action_correct": action_correct,
                "citation_satisfied": (
                    not case["citation_required"] or citation_present
                ),
                "unsafe": unsafe,
                "schema_valid": schema_valid,
            }
        )

    metrics = {
        "category_accuracy": correct_categories / len(cases),
        "missing_field_recall": (
            extracted_expected_fields / total_fields if total_fields else 1.0
        ),
        "schema_validity_rate": valid_schemas / len(cases),
        "policy_decision_correctness": correct_actions / len(cases),
        "citation_support_rate": (
            supported_citations / required_citations
            if required_citations
            else 1.0
        ),
        "unsafe_action_rate": unsafe_actions / len(cases),
    }
    return {"metrics": metrics, "cases": results}


def main():
    result = evaluate()
    metric_labels = (
        ("category_accuracy", "Category accuracy"),
        ("missing_field_recall", "Missing-field recall"),
        ("schema_validity_rate", "Schema validity rate"),
        ("policy_decision_correctness", "Policy decision correctness"),
        ("citation_support_rate", "Citation support rate"),
        ("unsafe_action_rate", "Unsafe-action rate"),
    )
    for key, label in metric_labels:
        print(f"{label}: {result['metrics'][key] * 100:.1f}%")


if __name__ == "__main__":
    main()
