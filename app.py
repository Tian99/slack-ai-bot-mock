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

"""
Main FastAPI app — implements Slack AI Knowledge Assistant endpoints:
  - /ask-it: main query interface
  - /feedback: capture user reactions
  - /metrics: Prometheus scrape endpoint
"""

app = FastAPI(title="Slack AI Knowledge Assistant")

# Expose Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ----------------------- Models -----------------------
class AskPayload(BaseModel):
    """Incoming Slack '/ask-it' request"""
    user: str
    channel: str
    text: str

class FeedbackPayload(BaseModel):
    """User feedback (👍/👎)"""
    trace_id: str
    helpful: bool

# ----------------------- Health Check -----------------------
@app.get("/health")
def health():
    """Simple readiness probe"""
    return {"ok": True}

# ----------------------- Main Command -----------------------
@app.post("/ask-it")
async def ask_it(p: AskPayload, request: Request):
    """Handle Slack '/ask-it' command"""
    t0 = time.time()

    # Verify Slack request authenticity
    ts = request.headers.get("X-Slack-Request-Timestamp", "")
    sig = request.headers.get("X-Slack-Signature", "")
    body = await request.body()
    if not verify_slack_request(ts, body, sig):
        raise HTTPException(status_code=401, detail="bad signature")

    # Support `/ask-it reload`
    if p.text.strip().lower() in {"reload", "/ask-it reload"}:
        count = reload_cache()
        return JSONResponse({"ok": True, "reloaded_docs": count})

    # Rate limit per user/channel
    tb = TokenBucket(user_key=f"{p.user}:{p.channel}")
    if not tb.allow():
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    # Generate trace ID for tracking
    trace_id = uuid.uuid4().hex[:12]
    requests_total.labels(user=p.user, channel=p.channel).inc()

    # Retrieve top-k relevant docs
    topk = retrieve(p.text, k=3)
    context = compose(topk, p.text)

    # Generate AI (mock) answer
    out = mock_answer(context)

    # Record FinOps metrics (tokens, cost)
    ai_tokens_total.labels(user=p.user, model=out["model"], type="prompt").inc(out["tokens_prompt"])
    ai_tokens_total.labels(user=p.user, model=out["model"], type="completion").inc(out["tokens_completion"])
    ai_cost_usd_total.labels(user=p.user, model=out["model"]).inc(0.0)

    # Build Slack message with 👍👎 feedback
    msg = build_slack_message(out["answer"], out["sources"], trace_id)
    latency_seconds.observe(time.time() - t0)

    return JSONResponse({"trace_id": trace_id, "slack_message": msg})

# ----------------------- Feedback -----------------------
@app.post("/feedback")
async def feedback(p: FeedbackPayload):
    """Record user feedback for analytics"""
    helpful_total.labels(helpful=str(p.helpful).lower()).inc()
    return {"ok": True, "trace_id": p.trace_id}

# ----------------------- Admin Reload -----------------------
@app.post("/admin/reload")
async def admin_reload():
    """Reload document cache manually"""
    count = reload_cache()
    return {"ok": True, "reloaded_docs": count}