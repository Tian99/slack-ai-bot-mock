from typing import Dict


def mock_answer(context: Dict) -> Dict:
    """
Mock AI answer generator.

This function simulates how an AI model (like GPT) would respond
based on retrieved document context. It returns a fake answer
with metadata so the system can be tested without calling a real API.

Args:
    context (Dict): Retrieved document snippets for the query.

Returns:
    Dict: Simulated answer with sources and token usage.
"""
    sources = [c["source"] for c in context.get("context", [])]
    answer = (
        "Based on local documentation, here are the relevant steps:\n"
        "- Step 1: Review the Okta MFA reset guide.\n"
        "- Step 2: If unresolved, try `/ask-it reload`.\n"
        "- Step 3: Contact IT if still locked out."
    )
    return {
        "answer": answer,
        "sources": sources,
        "tokens_prompt": 100,
        "tokens_completion": 60,
        "model": "mock"
    }
