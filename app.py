import time, uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from prometheus_client import make_asgi_app
from utils.slack_verifier import verify_slack_request
from utils.rate_limiter import TokenBucket
from ai.retriever import retrieve, compose, reload_cache
from ai.ai import mock_answer
from ai.response_builder import build_slack_message
from observability.metrics import (
    requests_total, latency_seconds, helpful_total,
    ai_tokens_total, ai_cost_usd_total
)

# -----------------------------------------------------------------------------
# Main FastAPI application entry point
# -----------------------------------------------------------------------------
app = FastAPI(title="Slack AI Knowledge Assistant")

# -----------------------------------------------------------------------------
# Expose Prometheus metrics endpoint under /metrics
# This allows Prometheus or Grafana Agent to scrape runtime telemetry data.
# -----------------------------------------------------------------------------
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# -----------------------------------------------------------------------------
# Request models for JSON payload validation
# -----------------------------------------------------------------------------
class AskPayload(BaseModel):
    """Represents a Slack command event."""
    user: str      # Slack user ID
    channel: str   # Slack channel ID
    text: str      # Command text, e.g. "reset okta mfa" or "reload"

class FeedbackPayload(BaseModel):
    """Represents a feedback button click event."""
    trace_id: str
    helpful: bool

# -----------------------------------------------------------------------------
# Health check endpoint (used for readiness / liveness probes)
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    """Simple health check."""
    return {"ok": True}

# -----------------------------------------------------------------------------
# Main /ask-it endpoint: core logic of the Slack Knowledge Assistant
# -----------------------------------------------------------------------------
@app.post("/ask-it")
async def ask_it(p: AskPayload, request: Request):
    """Handle Slack '/ask-it' command requests."""
    t0 = time.time()

    # --- Verify Slack signature (optional in mock mode)
    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")
    body = await request.body()
    if not verify_slack_request(ts, body, sig):
        raise HTTPException(status_code=401, detail="bad signature")

    # --- Hot reload: allow user to reload local documents via `/ask-it reload`
    if p.text.strip().lower() in {"reload", "/ask-it reload"}:
        count = reload_cache()
        return JSONResponse({"ok": True, "reloaded_docs": count})

    # --- Rate limiting per user/channel using Redis-based token bucket
    tb = TokenBucket(user_key=f"{p.user}:{p.channel}")
    if not tb.allow():
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    # --- Generate trace ID for observability and correlation
    trace_id = uuid.uuid4().hex[:12]
    requests_total.labels(user=p.user, channel=p.channel).inc()

    # --- Retrieve and compose contextual knowledge snippets
    topk = retrieve(p.text, k=3)
    context = compose(topk, p.text)

    # --- Mock AI layer generates response (can be replaced by real LLM)
    out = mock_answer(context)

    # --- Record AI token and cost metrics (for FinOps observability)
    ai_tokens_total.labels(user=p.user, model=out["model"], type="prompt").inc(out["tokens_prompt"])
    ai_tokens_total.labels(user=p.user, model=out["model"], type="completion").inc(out["tokens_completion"])
    ai_cost_usd_total.labels(user=p.user, model=out["model"]).inc(0.0)  # mock cost = 0

    # --- Format Slack Block Kit message for a nice visual response
    msg = build_slack_message(out["answer"], out["sources"], trace_id)

    # --- Record latency for performance metrics
    latency_seconds.observe(time.time() - t0)

    # --- Return the Slack-ready response payload
    return JSONResponse({
        "trace_id": trace_id,
        "slack_message": msg
    })

# -----------------------------------------------------------------------------
# /feedback endpoint: capture user feedback (👍 / 👎)
# -----------------------------------------------------------------------------
@app.post("/feedback")
async def feedback(p: FeedbackPayload):
    """
    Records feedback reaction.
    In production this could push to Kafka → ClickHouse for long-term analytics.
    """
    helpful_total.labels(helpful=str(p.helpful).lower()).inc()
    return {"ok": True, "trace_id": p.trace_id}

# -----------------------------------------------------------------------------
# /admin/reload endpoint: admin-only document cache reload
# Mirrors `/ask-it reload`, but can be called directly from automation or CI.
# -----------------------------------------------------------------------------
@app.post("/admin/reload")
async def admin_reload():
    """Reload cached knowledge base documents."""
    count = reload_cache()
    return {"ok": True, "reloaded_docs": count}
