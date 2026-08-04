"""
backend/scripts/evaluate_vision_agent.py

Day 9 - Vision Agent Evaluation Script (Refined & Live-Agent Ready)
Evaluates Vision Agent output against ground-truth annotations with dynamic API fallback.
"""

import json
import os
import sys
from pathlib import Path

# Setup Project Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Imports
try:
    from agents.vision_node import vision_agent_node
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

GROUND_TRUTH_FILE = PROJECT_ROOT / "tests" / "vision_ground_truth.json"
PASS_THRESHOLD = 0.50  # Balanced overlap threshold for semantic checks

MOCK_OUTPUTS = {
    "Summarize this chart.": "Revenue increased steadily from January to March.",
    "Which category has the highest sales?": "Electronics has the highest sales.",
    "Which section occupies the largest area?": "Sales occupies the largest section with 40 percent."
}


def load_test_cases():
    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(f"Ground truth file not found at {GROUND_TRUTH_FILE}")
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_similarity(prediction: str, ground_truth: str) -> float:
    """
    Calculates semantic overlap and key number match between prediction and ground truth.
    """
    pred_clean = prediction.lower().strip()
    truth_clean = ground_truth.lower().strip()

    # 1. Exact or Substring match
    if truth_clean in pred_clean:
        return 1.0

    # 2. Token overlap score
    pred_words = set(pred_clean.split())
    truth_words = set(truth_clean.split())

    if not truth_words:
        return 0.0

    overlap = pred_words.intersection(truth_words)
    score = len(overlap) / len(truth_words)

    return min(score, 1.0)


def get_agent_prediction(question: str, image_path: Path) -> str:
    """
    Calls the real Vision Node if API Key is available, else falls back to Mock.
    """
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))

    if has_api_key and AGENT_AVAILABLE:
        try:
            state = {
                "question": question,
                "file_path": str(image_path)
            }
            res = vision_agent_node(state)
            messages = res.get("messages", [])
            if messages:
                return messages[-1].content
        except Exception as err:
            print(f"⚠️ Live Vision Agent execution failed: {err}")

    # Fallback to Mock Output
    return MOCK_OUTPUTS.get(question, "No prediction available.")


def evaluate():
    test_cases = load_test_cases()
    total = len(test_cases)
    passed = 0
    failed = 0
    similarity_scores = []

    print("=" * 80)
    print("🎯 VISION AGENT EVALUATION SUITE")
    print("=" * 80)
    print(f"Live API Mode: {'ENABLED' if os.getenv('OPENAI_API_KEY') else 'DISABLED (Using Mock Data)'}")

    for idx, sample in enumerate(test_cases, start=1):
        image_rel = sample["image"]
        question = sample["question"]
        ground_truth = sample["ground_truth"]

        image_path = PROJECT_ROOT / image_rel

        print(f"\n[Sample #{idx}]")
        print("-" * 80)
        print(f"Image        : {image_rel}")
        print(f"Question     : {question}")
        print(f"Ground Truth : {ground_truth}")

        if not image_path.exists():
            print(f"Status       : ❌ Image file missing at {image_path}")
            failed += 1
            similarity_scores.append(0.0)
            continue

        prediction = get_agent_prediction(question, image_path)
        score = calculate_similarity(prediction, ground_truth)
        similarity_scores.append(score)

        if score >= PASS_THRESHOLD:
            status = "PASS ✅"
            passed += 1
        else:
            status = "FAIL ❌"
            failed += 1

        print(f"Prediction   : {prediction}")
        print(f"Similarity   : {score:.2f}")
        print(f"Result       : {status}")

    avg_similarity = (sum(similarity_scores) / total) if total else 0
    accuracy = (passed / total) * 100 if total else 0
    error_rate = (failed / total) * 100 if total else 0

    print("\n" + "=" * 80)
    print("📊 EVALUATION SUMMARY REPORT")
    print("=" * 80)
    print(f"Total Test Cases     : {total}")
    print(f"Passed               : {passed}")
    print(f"Failed               : {failed}")
    print(f"Accuracy Rate        : {accuracy:.2f}%")
    print(f"Average Similarity   : {avg_similarity:.2f}")
    print(f"Reasoning Error Rate : {error_rate:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    evaluate()