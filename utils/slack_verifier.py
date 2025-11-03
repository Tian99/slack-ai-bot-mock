import hmac, hashlib
from config import SLACK_SIGNING_SECRET

def verify_slack_request(timestamp: str, body: bytes, signature: str) -> bool:
    """Mock-friendly Slack signature verifier."""
    if not signature:
        return True  # mock mode: allow
    base = f"v0:{timestamp}:{body.decode('utf-8')}".encode("utf-8")
    my_sig = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode("utf-8"), base, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(my_sig, signature)
