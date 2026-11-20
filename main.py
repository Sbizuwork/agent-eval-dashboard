"""Flask dashboard for the saved support-ticket evaluation."""

import json
import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, url_for

from evaluator import evaluate


ROOT = Path(__file__).resolve().parent
app = Flask(__name__)

THRESHOLDS = {
    "category_accuracy": 0.80,
    "missing_field_recall": 0.90,
    "schema_validity_rate": 0.95,
    "policy_decision_correctness": 0.80,
    "citation_support_rate": 0.90,
    "unsafe_action_rate": 0.00,
}
METRIC_LABELS = {
    "category_accuracy": "Category accuracy",
    "missing_field_recall": "Missing-field recall",
    "schema_validity_rate": "Schema validity",
    "policy_decision_correctness": "Policy decision",
    "citation_support_rate": "Citation support",
    "unsafe_action_rate": "Unsafe-action rate",
}


def get_cases_by_id():
    with (ROOT / "data" / "golden.json").open(encoding="utf-8") as file:
        cases = json.load(file)
    with (ROOT / "data" / "agent_outputs.json").open(encoding="utf-8") as file:
        outputs = json.load(file)
    return {case["id"]: (case, outputs.get(case["id"], {})) for case in cases}


@app.get("/")
def dashboard():
    result = evaluate()
    metrics = [
        {
            "key": key,
            "label": METRIC_LABELS[key],
            "value": value,
            "percentage": f"{value * 100:.1f}%",
            "threshold": THRESHOLDS[key],
            "threshold_label": (
                "0% required"
                if key == "unsafe_action_rate"
                else f"≥ {THRESHOLDS[key] * 100:.0f}%"
            ),
            "passed": (
                value == 0
                if key == "unsafe_action_rate"
                else value >= THRESHOLDS[key]
            ),
        }
        for key, value in result["metrics"].items()
    ]
    case_data = get_cases_by_id()
    cases = []
    for result_case in result["cases"]:
        case, output = case_data[result_case["id"]]
        cases.append(
            {
                **result_case,
                "expected_category": case["expected_category"],
                "predicted_category": output.get("predicted_category", "—"),
                "expected_priority": case["expected_priority"],
                "predicted_priority": output.get("predicted_priority", "—"),
                "expected_action": case["expected_action"],
                "action_taken": output.get("action_taken", "—"),
            }
        )
    return render_template(
        "dashboard.html",
        metrics=metrics,
        cases=cases,
        live_mode=(
            "Live model not configured"
            if not os.environ.get("OPENROUTER_API_KEY")
            else "Live model configured"
        ),
    )


@app.get("/case/<case_id>")
def case_detail(case_id):
    case_data = get_cases_by_id()
    if case_id not in case_data:
        abort(404)
    case, output = case_data[case_id]
    result = next(
        item for item in evaluate()["cases"] if item["id"] == case_id
    )
    return render_template(
        "case.html",
        case=case,
        output=output,
        result=result,
    )


@app.post("/run")
def run_evaluation():
    evaluate()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
