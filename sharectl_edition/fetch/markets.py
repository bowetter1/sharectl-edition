"""Market indexes from Yahoo Finance's public chart endpoint. Optional module; may break if Yahoo changes it."""
import json
from datetime import datetime, timezone
from urllib.parse import quote

from .. import net


def fetch(cfg: dict) -> list[dict]:
    """cfg = {title, symbols: [{symbol, name, label}]}"""
    out = []
    for s in cfg.get("symbols", []):
        raw = net.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(s['symbol'])}?range=1d&interval=5m", 12, browser=True)
        try:
            r = json.loads(raw)["chart"]["result"][0]
            meta = r["meta"]
            closes = [c for c in r["indicators"]["quote"][0]["close"] if c is not None]
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            price = meta["regularMarketPrice"]
        except Exception:
            continue
        out.append({"label": s.get("label", s["symbol"]), "name": s.get("name", ""), "price": price, "prev": prev,
                    "change": (price - prev) / prev * 100 if prev else 0.0, "spark": closes or [price],
                    "time": datetime.fromtimestamp(meta.get("regularMarketTime", 0), timezone.utc).isoformat()})
    return out


def headline(ms: list[dict]) -> str:
    best = max(ms, key=lambda m: abs(m["change"]))
    verb = "rose" if best["change"] > 0 else "fell"
    return f"{best['label']} {verb} {abs(best['change']):.1f}%"
