from typing import Dict, List


"""
Build a Slack Block Kit message with answer, sources, trace_id, and feedback buttons.
"""

def build_slack_message(answer: str, sources: List[str], trace_id: str) -> Dict:
    src_text = "\n".join(f"• `{s}`" for s in sources) or "• (no sources)"
    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": answer}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*trace_id:* `{trace_id}`"}]},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Sources:*\n" + src_text}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "👍 Helpful"},
                 "value": f"{trace_id}|true", "action_id": "feedback_yes"},
                {"type": "button", "text": {"type": "plain_text", "text": "👎 Not helpful"},
                 "value": f"{trace_id}|false", "action_id": "feedback_no"}
            ]}
        ]
    }
