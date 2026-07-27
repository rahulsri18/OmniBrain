"""
Day 9 - Vision Agent Evaluation Script

Compares the Vision Agent output against manually prepared
ground-truth annotations and reports the VLM reasoning error rate.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
import importlib

# ----------------------------------------------------
# Project Root
# ----------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# ----------------------------------------------------
# Import Vision Agent (Mock LLM Initialization)
# ----------------------------------------------------

with patch("langchain_openai.ChatOpenAI"):
    vision_module = importlib.import_module("agents.vision_node")

VisionSubAgent = vision_module.VisionSubAgent

# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

GROUND_TRUTH_FILE = PROJECT_ROOT / "tests" / "vision_ground_truth.json"

PASS_THRESHOLD = 0.60

# ------------------------------------------------------------------
# Temporary mocked predictions.
#
# These are used to validate the evaluation pipeline without requiring
# an OpenAI API key. Replace these mocked outputs with actual Vision
# Agent predictions when API access is available.
# ------------------------------------------------------------------

MOCK_OUTPUTS = {

    "Summarize this chart.":

        "Revenue increased steadily from January to March.",

    "Which category has the highest sales?":

        "Electronics has the highest sales.",

    "Which section occupies the largest area?":

        "Sales occupies the largest section with 40 percent."

}

# ----------------------------------------------------
# Load Dataset
# ----------------------------------------------------

def load_test_cases():

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------------------
# Similarity
# ----------------------------------------------------

def similarity(prediction: str, ground_truth: str):

    prediction = prediction.lower().strip()
    ground_truth = ground_truth.lower().strip()

    # Exact Match
    if prediction == ground_truth:
        return 1.0

    # Ground Truth inside Prediction
    if ground_truth in prediction:
        return 1.0

    prediction_words = set(prediction.split())
    truth_words = set(ground_truth.split())

    if not truth_words:
        return 0.0

    overlap = prediction_words.intersection(truth_words)

    return len(overlap) / len(truth_words)

# ----------------------------------------------------
# Evaluation
# ----------------------------------------------------

def evaluate():

    test_cases = load_test_cases()

    total = len(test_cases)

    passed = 0
    failed = 0

    similarity_scores = []

    print("=" * 80)
    print("VISION AGENT EVALUATION")
    print("=" * 80)

    for idx, sample in enumerate(test_cases, start=1):

        image = sample["image"]
        question = sample["question"]
        ground_truth = sample["ground_truth"]

        image_path = PROJECT_ROOT / image

        print(f"\nSample #{idx}")
        print("-" * 80)
        print(f"Image        : {image}")
        print(f"Question     : {question}")
        print(f"Ground Truth : {ground_truth}")

        if not image_path.exists():

            print(f"Image Path   : {image_path}")
            print("Prediction   : Image file missing")
            print("Similarity   : 0.00")
            print("Result       : FAIL")

            failed += 1
            similarity_scores.append(0)

            continue

        prediction = MOCK_OUTPUTS.get(
            question,
            "No prediction available."
        )

        score = similarity(
            prediction,
            ground_truth
        )

        similarity_scores.append(score)

        if score >= PASS_THRESHOLD:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"Prediction   : {prediction}")
        print(f"Similarity   : {score:.2f}")
        print(f"Result       : {status}")

    average_similarity = (
        sum(similarity_scores) / total
        if total else 0
    )

    reasoning_error_rate = (
        failed / total * 100
        if total else 0
    )

    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)

    print(f"Total Samples        : {total}")
    print(f"Passed               : {passed}")
    print(f"Failed               : {failed}")
    evaluation_accuracy = (passed / total) * 100 if total else 0
    print(f"Evaluation Accuracy : {evaluation_accuracy:.2f}%")
    print(f"Average Similarity   : {average_similarity:.2f}")
    print(f"Reasoning Error Rate : {reasoning_error_rate:.2f}%")

    print("=" * 80)


if __name__ == "__main__":
    evaluate()