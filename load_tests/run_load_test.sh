#!/usr/bin/env bash
# load_tests/run_load_test.sh
# M1 Day 16: Headless Execution Script for Locust Load Testing

TARGET_HOST=${1:-"http://localhost:8000"}
USERS=${2:-50}
SPAWN_RATE=${3:-5}
RUN_TIME=${4:-"2m"}

echo "Running load test against $TARGET_HOST..."
echo "Simulating $USERS concurrent users (Spawn rate: $SPAWN_RATE/s) for $RUN_TIME"

locust -f load_tests/locustfile.py \
    --host="$TARGET_HOST" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="$RUN_TIME" \
    --headless \
    --html=load_tests/load_test_report.html \
    --csv=load_tests/load_test_results