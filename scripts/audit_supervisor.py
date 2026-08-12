"""
audit_supervisor.py

M1 Task (Day 9): Manual & Automated Audit of Supervisor Routing Decisions.
Runs sample queries through the LangGraph workflow and verifies node selection.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.logger import logger
from agents.graph import app_graph  # Compiled LangGraph Workflow


def audit_routing_decision(query: str, file_path: str = None) -> dict:
    """Executes a dry-run through the supervisor router and returns selected route."""
    logger.info(f"\n--- AUDITING QUERY: '{query}' | File: {file_path} ---")

    initial_state = {
        "messages": [{"role": "user", "content": query}],
        "session_id": "audit_test_session",
        "file_path": file_path,
        "next_node": ""
    }

    selected_route = "UNKNOWN"
    reasoning_steps = []

    try:
        # Stream events to inspect Supervisor routing
        for event in app_graph.stream(initial_state):
            for node_name, state_update in event.items():
                reasoning_steps.append(node_name)
                logger.info(f"📍 Executed Node: {node_name}")
                
                if "next_node" in state_update and state_update["next_node"]:
                    selected_route = state_update["next_node"]

        logger.info(f"✅ Final Routing Decision: {selected_route}")
        return {
            "query": query,
            "selected_route": selected_route,
            "steps": reasoning_steps,
            "status": "SUCCESS"
        }

    except Exception as e:
        logger.error(f"❌ Routing Audit Failed: {str(e)}")
        return {
            "query": query,
            "selected_route": "FAILED",
            "error": str(e),
            "status": "ERROR"
        }


if __name__ == "__main__":
    # Test Suite for Manual Audit
    test_cases = [
        {
            "category": "SQL / Structured Query",
            "query": "Show me the total revenue for Q3 from the sales database.",
            "expected": "sql_node"
        },
        {
            "category": "Vision / Chart Analysis",
            "query": "Explain the bar chart in this document.",
            "file_path": "tests/sample_chart.png",
            "expected": "vision_node"
        },
        {
            "category": "Unstructured RAG Query",
            "query": "What are the company policies regarding remote work?",
            "expected": "rag_node"
        }
    ]

    print("==================================================")
    print("🚀 STARTING DAY 9 SUPERVISOR ROUTING AUDIT")
    print("==================================================\n")

    for idx, test in enumerate(test_cases, 1):
        print(f"Test #{idx} [{test['category']}]")
        result = audit_routing_decision(query=test["query"], file_path=test.get("file_path"))
        print(f"Outcome: {result}\n" + "-"*50)