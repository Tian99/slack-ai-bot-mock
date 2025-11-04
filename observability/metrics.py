from prometheus_client import Counter, Histogram

"""
Prometheus metrics for Slack AI Assistant — used for observability and FinOps.
"""
requests_total = Counter(
    "askit_requests_total", "Total /ask-it requests", ["user", "channel"]
)
latency_seconds = Histogram(
    "askit_latency_seconds", "Latency of /ask-it end-to-end"
)
helpful_total = Counter(
    "askit_helpful_total", "Feedback helpful true/false", ["helpful"]
)
ai_tokens_total = Counter(
    "ai_tokens_total", "AI tokens by user and model", ["user", "model", "type"]
)
ai_cost_usd_total = Counter(
    "ai_cost_usd_total", "AI USD cost by user and model", ["user", "model"]
)
