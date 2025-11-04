import json, re
from pathlib import Path
from typing import List, Dict, Tuple
from config import DOCS_DIR

"""
Simple retriever module — loads local docs, caches them, and ranks by keyword match.
"""

_CACHE: Dict[str, str] = {}
_LOADED: bool = False

def _load_text(path: Path) -> str:
    """Load file content (.md / .txt / .json / .csv) as plain text."""
    if path.suffix.lower() in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".json":
        return json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False)
    if path.suffix.lower() == ".csv":
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""

def _scan_docs() -> Dict[str, str]:
    """Scan DOCS_DIR and load all supported documents into memory."""
    d: Dict[str, str] = {}
    p = Path(DOCS_DIR)
    if not p.exists():
        return d
    for f in p.glob("*"):
        if f.is_file() and f.suffix.lower() in {".md", ".txt", ".json", ".csv"}:
            d[str(f)] = _load_text(f)
    return d

def ensure_loaded() -> None:
    """Load cache once on first use."""
    global _LOADED, _CACHE
    if not _LOADED:
        _CACHE = _scan_docs()
        _LOADED = True

def reload_cache() -> int:
    """Force reload all documents."""
    global _CACHE, _LOADED
    _CACHE = _scan_docs()
    _LOADED = True
    return len(_CACHE)

def get_docs() -> Dict[str, str]:
    """Return cached document store."""
    ensure_loaded()
    return _CACHE

def _score(query: str, text: str) -> float:
    """Simple keyword scoring: match count + bonus for early matches."""
    q = [w.lower() for w in re.findall(r"[a-zA-Z0-9_]+", query)]
    t = text.lower()
    base = sum(t.count(w) for w in q)
    head_bonus = sum(t[:400].count(w) for w in q) * 0.5
    return base + head_bonus

def retrieve(query: str, k=3) -> List[Tuple[str, float]]:
    """Return top-k matching docs ranked by relevance score."""
    docs = get_docs()
    ranked = sorted(((path, _score(query, body)) for path, body in docs.items()),
                    key=lambda x: x[1], reverse=True)
    return [(p, s) for p, s in ranked[:k] if s > 0]

def compose(snippets: List[Tuple[str, float]], query: str) -> Dict:
    """Build context payload combining top results and excerpts."""
    ctx = []
    docs = get_docs()
    for path, _ in snippets:
        body = docs.get(path, "")[:800]
        ctx.append({"source": path, "excerpt": body})
    return {"query": query, "context": ctx}
