from typing import Dict

def mock_answer(context: Dict) -> Dict:
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
