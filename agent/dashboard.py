#!/usr/bin/env python3
"""
Dashboard de Riesgo y Calidad - Agent Karate
Interfaz Gradio refinada con estética minimalista dark.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
import json

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import gradio as gr
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    from pymongo import MongoClient
except ImportError as e:
    raise ImportError(f"Missing dependencies: {e}\nInstall: pip install gradio plotly pandas pymongo")

try:
    from .mongo_sync import MongoSync
except ImportError:
    try:
        from agent.mongo_sync import MongoSync
    except ImportError as e:
        print(f"Error importando mongo_sync: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# PALETA — Dark minimalista tipo Linear/Vercel
# Alto contraste · Semántica clara · QA-first
# ─────────────────────────────────────────────
P = {
    # Base — azul-gris oscuro, no negro puro
    "bg":           "#0f1117",
    "surface":      "#1a1d27",
    "surface2":     "#13151f",
    "surface3":     "#222636",

    # Tipografía — contraste alto
    "text":         "#f0f2f5",
    "text_sec":     "#b8c0cc",
    "muted":        "#6b7280",

    # Bordes
    "border":       "#2a2d3e",
    "border_lt":    "#1e2030",

    # Acento primario — azul eléctrico
    "accent":       "#4f8ef7",
    "accent_lt":    "#82b0ff",
    "accent_glow":  "rgba(79, 142, 247, 0.15)",

    # OK / PASS — verde lima vibrante (GitHub Actions style)
    "ok":           "#4ade80",
    "ok_light":     "rgba(74, 222, 128, 0.15)",
    "ok_border":    "rgba(74, 222, 128, 0.35)",

    # WARN / MEDIUM — ámbar cálido
    "warn":         "#f5a623",
    "warn_light":   "rgba(245, 166, 35, 0.15)",
    "warn_border":  "rgba(245, 166, 35, 0.35)",

    # CRIT / FAIL — rojo coral
    "crit":         "#ff5c5c",
    "crit_light":   "rgba(255, 92, 92, 0.15)",
    "crit_border":  "rgba(255, 92, 92, 0.35)",

    # Info
    "info":         "#4f8ef7",

    # Efectos
    "shadow":       "rgba(0, 0, 0, 0.4)",
    "shadow_sm":    "rgba(0, 0, 0, 0.2)",
}


PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#13151f",
    font=dict(
        family="'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif",
        color="#b8c0cc",
        size=12,
    ),
    title_font=dict(
        family="'DM Sans', sans-serif",
        color="#f0f2f5",
        size=15,
        weight=600,
    ),
    xaxis=dict(
        showgrid=True, gridwidth=1, gridcolor="#2a2d3e",
        zeroline=False, color="#6b7280",
        tickfont=dict(size=11, color="#6b7280"),
        linecolor="#2a2d3e", linewidth=1,
    ),
    yaxis=dict(
        showgrid=True, gridwidth=1, gridcolor="#2a2d3e",
        zeroline=False, color="#6b7280",
        tickfont=dict(size=11, color="#6b7280"),
        linecolor="#2a2d3e", linewidth=1,
    ),
    legend=dict(
        bgcolor="rgba(26, 29, 39, 0.95)",
        bordercolor="#2a2d3e", borderwidth=1,
        font=dict(size=11, color="#b8c0cc", family="'DM Sans', sans-serif"),
        x=0.01, y=0.99,
    ),
    hoverlabel=dict(
        bgcolor="#1a1d27",
        bordercolor="#4f8ef7",
        font=dict(family="'DM Sans', sans-serif", size=12, color="#f0f2f5"),
        align="left",
    ),
    margin=dict(t=50, b=40, l=50, r=20),
)


CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, .gradio-container {{
  background: {P['bg']} !important;
  color: {P['text']} !important;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

@keyframes fadeUp {{
  from {{ opacity: 0; transform: translateY(6px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes tabIn {{
  from {{ opacity: 0; }}
  to   {{ opacity: 1; }}
}}

.header {{
  padding: 40px 0 28px;
  border-bottom: 1px solid {P['border']};
  margin-bottom: 28px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}}
.dash-title {{
  font-size: 26px !important;
  font-weight: 700 !important;
  color: {P['text']} !important;
  letter-spacing: -0.8px;
}}
.dash-sub {{
  font-size: 11px !important;
  color: {P['muted']} !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 6px !important;
  font-weight: 500;
}}
.header-right {{
  font-size: 12px;
  color: {P['muted']};
}}

.tab-nav {{
  background: transparent !important;
  border-bottom: 1px solid {P['border']} !important;
  gap: 24px !important;
  padding: 0 !important;
}}
.tab-nav button {{
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  color: {P['muted']} !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  padding: 10px 0 !important;
  border-radius: 0 !important;
  margin-bottom: -1px;
  transition: color 0.2s, border-color 0.2s !important;
  cursor: pointer;
}}
.tab-nav button:hover {{
  color: {P['text_sec']} !important;
}}
.tab-nav button.selected {{
  color: {P['text']} !important;
  border-bottom-color: {P['accent']} !important;
  animation: tabIn 0.25s ease-out !important;
}}
.tabitem {{
  background: transparent !important;
  border: none !important;
  padding: 24px 0 !important;
}}

.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 28px;
}}
.kpi-card {{
  background: {P['surface']} !important;
  border: 1px solid {P['border']} !important;
  border-radius: 10px !important;
  padding: 18px !important;
  box-shadow: 0 2px 8px {P['shadow_sm']} !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  animation: fadeUp 0.4s ease-out !important;
}}
.kpi-card:hover {{
  border-color: {P['accent']} !important;
  box-shadow: 0 0 0 1px {P['accent']}, 0 4px 16px {P['accent_glow']} !important;
}}
.kpi-label {{
  font-size: 11px !important;
  letter-spacing: 0.8px !important;
  text-transform: uppercase !important;
  color: {P['muted']} !important;
  margin-bottom: 10px;
  font-weight: 600;
}}
.kpi-value {{
  font-family: 'DM Mono', monospace !important;
  font-size: 34px !important;
  font-weight: 500 !important;
  line-height: 1;
  letter-spacing: -0.5px;
}}
.kpi-value.ok   {{ color: {P['ok']}     !important; }}
.kpi-value.warn {{ color: {P['warn']}   !important; }}
.kpi-value.crit {{ color: {P['crit']}   !important; }}
.kpi-value.base {{ color: {P['accent']} !important; }}

.risk-card {{
  background: {P['surface']};
  border: 1px solid {P['border']};
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 2px 6px {P['shadow_sm']};
  transition: transform 0.2s, box-shadow 0.2s;
  animation: fadeUp 0.4s ease-out;
}}
.risk-card:hover {{
  transform: translateY(-1px);
  box-shadow: 0 4px 14px {P['shadow']};
}}
.risk-card.critical {{
  border-left: 3px solid {P['crit']};
  background: linear-gradient(90deg, {P['crit_light']} 0%, transparent 60%);
}}
.risk-card.medium {{
  border-left: 3px solid {P['warn']};
  background: linear-gradient(90deg, {P['warn_light']} 0%, transparent 60%);
}}
.risk-card.low {{
  border-left: 3px solid {P['ok']};
  background: linear-gradient(90deg, {P['ok_light']} 0%, transparent 60%);
}}
.risk-meta {{
  font-size: 11px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: {P['muted']};
  margin-bottom: 6px;
  font-weight: 600;
}}
.risk-body {{
  font-size: 13px;
  color: {P['text_sec']};
  line-height: 1.55;
}}

.badge {{
  display: inline-block;
  font-size: 10px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 5px;
}}
.badge.ok   {{ background: {P['ok_light']};    color: {P['ok']};    border: 1px solid {P['ok_border']};   }}
.badge.warn {{ background: {P['warn_light']};  color: {P['warn']};  border: 1px solid {P['warn_border']}; }}
.badge.crit {{ background: {P['crit_light']};  color: {P['crit']};  border: 1px solid {P['crit_border']}; }}
.badge.info {{ background: {P['accent_glow']}; color: {P['accent']}; border: 1px solid {P['accent']};     }}

.refresh-btn {{
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  background: {P['surface']} !important;
  border: 1px solid {P['border']} !important;
  color: {P['text_sec']} !important;
  border-radius: 6px !important;
  padding: 7px 14px !important;
  transition: all 0.2s !important;
}}
.refresh-btn:hover {{
  border-color: {P['accent']} !important;
  color: {P['accent']} !important;
}}

input[type="radio"], input[type="range"] {{ accent-color: {P['accent']} !important; }}
label {{
  color: {P['text_sec']} !important;
  font-weight: 600 !important;
  font-size: 13px !important;
}}
*:focus {{
  outline: none !important;
  box-shadow: 0 0 0 2px {P['accent_glow']} !important;
}}

.dataframe {{ font-family: 'DM Sans', sans-serif !important; }}
.dataframe th {{
  background: {P['surface2']} !important;
  color: {P['muted']} !important;
  font-size: 10px !important;
  letter-spacing: 0.8px !important;
  text-transform: uppercase !important;
  padding: 10px 14px !important;
  border: none !important;
  border-bottom: 1px solid {P['border']} !important;
  font-weight: 700;
}}
.dataframe td {{
  background: {P['surface']} !important;
  color: {P['text_sec']} !important;
  padding: 10px 14px !important;
  border-bottom: 1px solid {P['border_lt']} !important;
  font-size: 13px !important;
  font-family: 'DM Mono', monospace !important;
}}
.dataframe tr:hover td {{
  background: {P['surface3']} !important;
  color: {P['text']} !important;
}}

.plot-container {{
  background: {P['surface']} !important;
  border: 1px solid {P['border']} !important;
  border-radius: 8px !important;
  overflow: hidden !important;
  box-shadow: 0 2px 8px {P['shadow_sm']} !important;
}}

.section-label {{
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: {P['muted']};
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid {P['border']};
  font-weight: 700;
}}

footer, .show-api {{ display: none !important; }}
"""


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _layout(title="", height=400, **kw):
    base = dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(color=P["text"], size=14, family="'DM Sans', sans-serif"),
        ),
        font=dict(family="'DM Sans', sans-serif", color=P["text_sec"], size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=P["surface2"],
        xaxis=dict(
            color=P["muted"], showgrid=True, gridcolor=P["border"],
            zeroline=False, tickfont=dict(color=P["muted"], size=11),
            linecolor=P["border"],
        ),
        yaxis=dict(
            color=P["muted"], showgrid=True, gridcolor=P["border"],
            zeroline=False, tickfont=dict(color=P["muted"], size=11),
            linecolor=P["border"],
        ),
        legend=dict(
            bgcolor="rgba(26,29,39,0.95)", bordercolor=P["border"], borderwidth=1,
            font=dict(size=11, color=P["text_sec"]),
        ),
        hoverlabel=dict(
            bgcolor=P["surface"], bordercolor=P["accent"],
            font=dict(size=12, color=P["text"]),
        ),
        margin=dict(t=50, b=40, l=50, r=20),
        height=height,
        hovermode="x unified",
        showlegend=False,
    )
    base.update(kw)
    return base


def _risk_color(risk_str: str) -> str:
    return {
        "CRITICAL": P["crit"],
        "MEDIUM":   P["warn"],
        "LOW":      P["ok"],
    }.get(risk_str, P["ok"])


# ─────────────────────────────────────────────
# DashboardQueries
# ─────────────────────────────────────────────
class DashboardQueries:
    def __init__(self, mongo_sync):
        self.mongo = mongo_sync
        if not mongo_sync.enabled:
            raise RuntimeError("MongoDB no disponible.")
        self.db = mongo_sync.db

    def get_latest_executions(self, limit=10, days=30):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["execution_summaries"]
            results = list(col.find({"run_date": {"$gte": start}}).sort("run_date", -1).limit(limit))
            if not results:
                return []
            for doc in results:
                doc["_id"] = str(doc["_id"])
                doc["run_date"] = doc["run_date"].isoformat()
                branch = doc.get("branch", "unknown")
                if not branch or (isinstance(branch, (int, float))):
                    pr_num = doc.get("pr_number", "unknown")
                    doc["branch"] = f"PR-{pr_num}" if pr_num != "unknown" else str(branch)
                else:
                    doc["branch"] = str(branch)
            return results
        except Exception as e:
            print(f"Error get_latest_executions: {e}"); return []

    def get_kpis_summary(self, days=30):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["execution_summaries"]
            print(f"[DEBUG] get_kpis_summary: days={days}, start={start}")
            pipeline = [
                {"$match": {"run_date": {"$gte": start}}},
                {"$group": {
                    "_id": None,
                    "total_tests":    {"$sum": "$total_tests"},
                    "passed_tests":   {"$sum": "$passed_tests"},
                    "failed_tests":   {"$sum": "$failed_tests"},
                    "avg_pass_rate":  {"$avg": "$overall_pass_rate"},
                    "critical_count": {"$sum": {"$cond": [{"$eq": ["$overall_risk_level","CRITICAL"]}, 1, 0]}},
                }},
            ]
            r = list(col.aggregate(pipeline))
            print(f"[DEBUG] get_kpis_summary result count: {len(r)}, data: {r}")
            if r and r[0].get("total_tests", 0) > 0:
                d = r[0]; rate = d["avg_pass_rate"]
                risk = "LOW" if rate == 100 else "MEDIUM" if rate >= 90 else "CRITICAL"
                return {"total_tests": int(d["total_tests"]), "passed_tests": int(d["passed_tests"]),
                        "failed_tests": int(d["failed_tests"]), "overall_pass_rate": round(rate, 2),
                        "overall_risk_level": risk, "critical_runs": int(d["critical_count"])}
            print(f"[DEBUG] get_kpis_summary returning empty KPI")
            return {"total_tests":0,"passed_tests":0,"failed_tests":0,"overall_pass_rate":0,
                    "overall_risk_level":"UNKNOWN","critical_runs":0}
        except Exception as e:
            print(f"Error get_kpis_summary: {e}"); return {}

    def get_branch_trending(self, days=30, limit_branches=5):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["execution_summaries"]
            print(f"[DEBUG] get_branch_trending: days={days}, start={start}")
            count = col.count_documents({"run_date": {"$gte": start}})
            print(f"[DEBUG] get_branch_trending found {count} documents")
            if count == 0:
                print(f"[DEBUG] get_branch_trending returning empty dataframe")
                return pd.DataFrame()
            top = [b["_id"] for b in col.aggregate([
                {"$match": {"run_date": {"$gte": start}}},
                {"$group": {"_id": "$branch", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}, {"$limit": limit_branches},
            ])]
            if not top: return pd.DataFrame()
            data = [{"date": r["_id"]["date"], "branch": r["_id"]["branch"],
                     "pass_rate": round(r["avg_pass_rate"], 2)}
                    for r in col.aggregate([
                        {"$match": {"run_date": {"$gte": start}, "branch": {"$in": top}}},
                        {"$group": {"_id": {"branch": "$branch",
                                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$run_date"}}},
                                    "avg_pass_rate": {"$avg": "$overall_pass_rate"}}},
                        {"$sort": {"_id.date": 1}},
                    ])]
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error get_branch_trending: {e}"); return pd.DataFrame()

    def get_feature_stats(self, days=30):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["test_results"]
            print(f"[DEBUG] get_feature_stats: days={days}, start={start}")
            count = col.count_documents({"run_date": {"$gte": start}})
            print(f"[DEBUG] get_feature_stats found {count} documents")
            return [{"feature": d["_id"], "total_tests": int(d["total"]),
                     "passed": int(d["passed"]), "failed": int(d["failed"]),
                     "pass_rate": round(d["passed"]/d["total"]*100 if d["total"] else 0, 2),
                     "avg_duration_ms": round(d["avg_duration_ms"], 2)}
                    for d in col.aggregate([
                        {"$match": {"run_date": {"$gte": start}}},
                        {"$group": {"_id": "$feature", "total": {"$sum": 1},
                                    "passed": {"$sum": {"$cond": [{"$eq":["$status","passed"]},1,0]}},
                                    "failed": {"$sum": {"$cond": [{"$eq":["$status","failed"]},1,0]}},
                                    "avg_duration_ms": {"$avg": "$duration_ms"}}},
                        {"$sort": {"total": -1}},
                    ])]
        except Exception as e:
            print(f"Error get_feature_stats: {e}"); return []

    def get_flaky_tests(self, days=30, min_flakiness=0.3, limit=20):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["test_results"]
            return [{"test_id": d["test_id"], "flakiness_pct": round(d["flakiness"]*100, 1),
                     "failure_count": int(d["failure_count"]), "total_runs": int(d["total_runs"]),
                     "last_run_date": d["last_run_date"].isoformat() if d["last_run_date"] else "N/A"}
                    for d in col.aggregate([
                        {"$match": {"run_date": {"$gte": start}}},
                        {"$group": {"_id": "$test_id", "total": {"$sum": 1},
                                    "failed": {"$sum": {"$cond": [{"$eq":["$status","failed"]},1,0]}},
                                    "last_run_date": {"$max": "$run_date"}}},
                        {"$project": {"test_id": "$_id", "flakiness": {"$divide":["$failed","$total"]},
                                      "failure_count": "$failed", "total_runs": "$total", "last_run_date": 1}},
                        {"$match": {"flakiness": {"$gte": min_flakiness}}},
                        {"$sort": {"flakiness": -1}}, {"$limit": limit},
                    ])]
        except Exception as e:
            print(f"Error get_flaky_tests: {e}"); return []

    def get_ai_blockers(self, days=30, limit=10):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["execution_summaries"]
            return [{"pr_number": doc.get("pr_number","N/A"), "branch": doc.get("branch","unknown"),
                     "overall_risk_level": doc.get("overall_risk_level"),
                     "ai_blockers": ", ".join(doc.get("ai_blockers",[])) or "None",
                     "run_date": doc["run_date"].isoformat()}
                    for doc in col.find({"run_date": {"$gte": start},
                                         "ai_blockers": {"$exists": True, "$ne": []}})
                    .sort("run_date", -1).limit(limit)]
        except Exception as e:
            print(f"Error get_ai_blockers: {e}"); return []

    def get_daily_pass_rate(self, days=30):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["execution_summaries"]
            print(f"[DEBUG] get_daily_pass_rate: days={days}, start={start}")
            count = col.count_documents({"run_date": {"$gte": start}})
            print(f"[DEBUG] get_daily_pass_rate found {count} documents")
            return pd.DataFrame([{"date": d["_id"],
                                   "pass_rate": round(d["avg_pass_rate"], 2),
                                   "risk_level": d["most_common_risk"]}
                                  for d in col.aggregate([
                                      {"$match": {"run_date": {"$gte": start}}},
                                      {"$group": {"_id": {"$dateToString": {"format":"%Y-%m-%d","date":"$run_date"}},
                                                  "avg_pass_rate": {"$avg": "$overall_pass_rate"},
                                                  "most_common_risk": {"$first": "$overall_risk_level"}}},
                                      {"$sort": {"_id": 1}},
                                  ])])
        except Exception as e:
            print(f"Error get_daily_pass_rate: {e}"); return pd.DataFrame()

    def get_current_cycle(self):
        try:
            col = self.db["test_cycles"]
            cycle = col.find_one({"status": {"$in": ["In Progress", "Active"]}}, sort=[("start_date", -1)])
            if not cycle:
                return None
            cycle["_id"] = str(cycle["_id"])
            if "start_date" in cycle and hasattr(cycle["start_date"], "isoformat"):
                cycle["start_date"] = cycle["start_date"].isoformat()
            if "end_date" in cycle and hasattr(cycle["end_date"], "isoformat"):
                cycle["end_date"] = cycle["end_date"].isoformat()
            return cycle
        except Exception as e:
            print(f"Error get_current_cycle: {e}"); return None


# ─────────────────────────────────────────────
# DashboardUI
# ─────────────────────────────────────────────
class DashboardUI:
    def __init__(self, queries):
        self.queries = queries
        self._ct, self._cd = {}, {}

    def _cached(self, key, fn, ttl=60, **kw):
        now = datetime.now(timezone.utc)
        cache_key = f"{key}_{str(sorted(kw.items()))}"
        if cache_key in self._ct and (now - self._ct[cache_key]).total_seconds() < ttl:
            return self._cd[cache_key]
        try:
            data = fn(**kw)
            self._ct[cache_key] = now
            self._cd[cache_key] = data
            return data
        except Exception as e:
            print(f"Error in _cached({key}): {e}")
            if "kpis" in key:
                return {"total_tests":0,"passed_tests":0,"failed_tests":0,"overall_pass_rate":0,
                        "overall_risk_level":"UNKNOWN","critical_runs":0}
            return [] if isinstance(fn.__name__, str) and "list" in fn.__name__ else pd.DataFrame()

    def refresh_cache(self):
        self._ct.clear(); self._cd.clear()

    # ── Overview ──
    def tab_overview(self, days=30):
        from datetime import datetime as dt_class

        kpis       = self._cached("kpis",      self.queries.get_kpis_summary,     days=days)
        last_execs = self._cached("last_exec",  self.queries.get_latest_executions, limit=5, days=days)
        blockers   = self._cached("blockers",   self.queries.get_ai_blockers,       ttl=120, days=days, limit=3)
        cycle      = self._cached("cycle",      self.queries.get_current_cycle,     ttl=300)
        flaky      = self._cached("flaky_ov",   self.queries.get_flaky_tests,       ttl=120, days=days, limit=5)

        last_run = last_execs[0] if last_execs else None
        last_pass_rate = last_run.get("overall_pass_rate", 100) if last_run else 100

        time_since_last = "N/A"
        if last_run and "run_date" in last_run:
            try:
                run_date_str = str(last_run["run_date"])
                if "T" in run_date_str:
                    run_date_str = run_date_str.split(".")[0] if "." in run_date_str else run_date_str
                    run_date_str = run_date_str.replace("Z", "+00:00")
                    run_dt = dt_class.fromisoformat(run_date_str)
                else:
                    run_dt = dt_class.fromisoformat(run_date_str)
                if run_dt.tzinfo is None:
                    run_dt = run_dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = now - run_dt
                mins = int(delta.total_seconds() / 60)
                if mins < 60:
                    time_since_last = f"hace {mins} min"
                elif mins < 1440:
                    time_since_last = f"hace {mins // 60} h"
                else:
                    time_since_last = f"hace {mins // 1440} d"
            except Exception as te:
                print(f"Error parsing time: {te}")

        last_run_risk = last_run.get("overall_risk_level", "UNKNOWN") if last_run else "UNKNOWN"
        has_critical_blockers = (last_run_risk == "CRITICAL" and last_pass_rate < 100)
        last_exec_old = False
        if last_run:
            try:
                run_dt = dt_class.fromisoformat(str(last_run["run_date"]).replace("Z", "+00:00"))
                if run_dt.tzinfo is None:
                    run_dt = run_dt.replace(tzinfo=timezone.utc)
                last_exec_old = (datetime.now(timezone.utc) - run_dt).total_seconds() / 3600 > 48
            except:
                pass

        if not last_run:
            estado, estado_color = "SIN DATOS", P["muted"]
        elif last_pass_rate < 70 or has_critical_blockers:
            estado, estado_color = "BLOQUEADO", P["crit"]
        elif last_pass_rate < 90 or last_exec_old:
            estado, estado_color = "ATENCIÓN REQUERIDA", P["warn"]
        else:
            estado, estado_color = "SISTEMA SALUDABLE", P["ok"]

        lr_total  = last_run.get("total_tests", 0)  if last_run else 0
        lr_passed = last_run.get("passed_tests", 0) if last_run else 0
        lr_failed = last_run.get("failed_tests", 0) if last_run else 0

        estado_html = f"""
<div style="background:{P['surface']};border:1px solid {P['border_lt']};border-radius:10px;padding:28px;margin-bottom:32px;box-shadow:0 2px 8px {P['shadow']}">
  <div style="display:flex;gap:28px;align-items:stretch">
    <div style="flex:1;display:flex;flex-direction:column;justify-content:center">
      <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:{P['muted']};margin-bottom:8px;font-weight:700">Última Ejecución · {time_since_last}</div>
      <div style="font-size:44px;font-weight:700;color:{estado_color};font-family:'DM Sans',sans-serif;letter-spacing:-1px;line-height:1.1;margin-bottom:4px">{estado}</div>
      <div style="font-size:13px;color:{P['text_sec']};line-height:1.6">Sistema de <span style="font-weight:600">pruebas automatizadas</span> para Karate Framework</div>
    </div>
    <div style="display:flex;gap:24px;align-items:center;padding-left:28px;border-left:1px solid {P['border_lt']}">
      <div style="text-align:center">
        <div style="font-size:10px;letter-spacing:0.8px;text-transform:uppercase;color:{P['muted']};margin-bottom:6px;font-weight:700">Total</div>
        <div style="font-size:34px;color:{P['text']};font-weight:600;font-family:'DM Mono',monospace;line-height:1">{lr_total}</div>
      </div>
      <div style="text-align:center">
        <div style="font-size:10px;letter-spacing:0.8px;text-transform:uppercase;color:{P['muted']};margin-bottom:6px;font-weight:700">OK</div>
        <div style="font-size:34px;color:{P['ok']};font-weight:600;font-family:'DM Mono',monospace;line-height:1">{lr_passed}</div>
      </div>
      <div style="text-align:center">
        <div style="font-size:10px;letter-spacing:0.8px;text-transform:uppercase;color:{P['muted']};margin-bottom:6px;font-weight:700">FAIL</div>
        <div style="font-size:34px;color:{P['crit']};font-weight:600;font-family:'DM Mono',monospace;line-height:1">{lr_failed}</div>
      </div>
      <div style="text-align:center">
        <div style="font-size:10px;letter-spacing:0.8px;text-transform:uppercase;color:{P['muted']};margin-bottom:6px;font-weight:700">Éxito</div>
        <div style="font-size:34px;color:{estado_color};font-weight:600;font-family:'DM Mono',monospace;line-height:1">{last_pass_rate}%</div>
      </div>
    </div>
  </div>
</div>"""

        rate  = kpis.get("overall_pass_rate", 0)
        risk  = kpis.get("overall_risk_level", "UNKNOWN")
        rc    = "ok" if rate == 100 else "warn" if rate >= 90 else "crit"
        riskc = "ok" if risk == "LOW" else "warn" if risk == "MEDIUM" else "crit"

        kpi_html = f"""
<div class="section-label" style="margin-top:36px">Historial acumulado · últimos {days} días</div>
<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-label">Total Tests</div><div class="kpi-value base">{kpis.get('total_tests',0)}</div></div>
  <div class="kpi-card"><div class="kpi-label">Exitosos</div><div class="kpi-value ok">{kpis.get('passed_tests',0)}</div></div>
  <div class="kpi-card"><div class="kpi-label">Fallidos</div><div class="kpi-value crit">{kpis.get('failed_tests',0)}</div></div>
  <div class="kpi-card"><div class="kpi-label">% Éxito Prom.</div><div class="kpi-value {rc}">{rate}%</div></div>
  <div class="kpi-card"><div class="kpi-label">Nivel de Riesgo</div><div class="kpi-value {riskc}">{risk}</div></div>
  <div class="kpi-card"><div class="kpi-label">Runs Críticos</div><div class="kpi-value warn">{kpis.get('critical_runs',0)}</div></div>
</div>"""

        recent_html = f"<div class='section-label' style='margin-top:28px'>Últimas Ejecuciones</div>"
        if last_execs:
            recent_rows = f"<table style='width:100%;border-collapse:collapse;margin-bottom:28px;border-radius:8px;overflow:hidden;border:1px solid {P['border']}'>"
            recent_rows += f"<tr style='background:{P['surface2']}'>"
            for header in ["RAMA / PR", "ÉXITO", "RIESGO", "HACE"]:
                recent_rows += f"<th style='padding:10px 14px;font-size:10px;letter-spacing:0.8px;text-transform:uppercase;color:{P['muted']};text-align:left;font-weight:700;border-bottom:1px solid {P['border']}'>{header}</th>"
            recent_rows += "</tr>"

            for ex in last_execs[:5]:
                branch    = ex.get("branch", "N/A")
                pass_rate = round(float(ex.get("overall_pass_rate", 0)), 1)
                risk      = ex.get("overall_risk_level", "LOW")
                run_date  = ex.get("run_date", "N/A")
                time_rel  = "N/A"
                try:
                    run_date_str = str(run_date)
                    if "T" in run_date_str:
                        run_date_str = run_date_str.split(".")[0] if "." in run_date_str else run_date_str
                        run_date_str = run_date_str.replace("Z", "+00:00")
                        run_dt = dt_class.fromisoformat(run_date_str)
                    else:
                        run_dt = dt_class.fromisoformat(run_date_str)
                    if run_dt.tzinfo is None:
                        run_dt = run_dt.replace(tzinfo=timezone.utc)
                    mins = int((datetime.now(timezone.utc) - run_dt).total_seconds() / 60)
                    if mins < 60:    time_rel = f"{mins} min"
                    elif mins < 1440: time_rel = f"{mins // 60} h"
                    else:             time_rel = f"{mins // 1440} d"
                except Exception as e:
                    print(f"Error calc time_rel: {e}")

                risk_color = _risk_color(risk)
                risk_bg    = P["ok_light"] if risk == "LOW" else P["warn_light"] if risk == "MEDIUM" else P["crit_light"]

                recent_rows += f"""<tr style='border-bottom:1px solid {P['border_lt']};background:{P['surface']}'>
                    <td style='padding:11px 14px;font-size:13px;color:{P['text']};font-weight:500'>{branch}</td>
                    <td style='padding:11px 14px;font-size:13px;color:{P['text']};font-family:DM Mono,monospace;font-weight:600'>{pass_rate}%</td>
                    <td style='padding:11px 14px'><span style='background:{risk_bg};color:{risk_color};padding:3px 8px;border-radius:5px;font-size:10px;letter-spacing:0.8px;text-transform:uppercase;font-weight:700;border:1px solid {risk_color}'>{risk}</span></td>
                    <td style='padding:11px 14px;font-size:13px;color:{P['muted']};font-family:DM Mono,monospace'>{time_rel}</td>
                </tr>"""
            recent_rows += "</table>"
            recent_html += recent_rows
        else:
            recent_html += f"<p style='color:{P['muted']};font-size:14px;margin-bottom:28px'>Sin ejecuciones en este período</p>"

        cycle_html = ""
        if cycle:
            cycle_name   = cycle.get("cycle_name", "Unknown")
            sprint       = cycle.get("sprint", "N/A")
            start_date   = cycle.get("start_date", "N/A")[:10] if cycle.get("start_date") else "N/A"
            end_date     = cycle.get("end_date", "N/A")[:10]   if cycle.get("end_date")   else "N/A"
            planned      = cycle.get("total_tests_planned", 0)
            executed     = cycle.get("tests_executed", 0)
            progress     = round(executed/planned*100) if planned > 0 else 0
            cycle_status = cycle.get("status", "Unknown")
            status_color = P["ok"] if cycle_status == "Active" else P["warn"] if cycle_status == "In Progress" else P["muted"]

            cycle_html = f"""
<div class="section-label" style="margin-top:28px">Ciclo en Progreso</div>
<div style="background:{P['surface']};border:1px solid {P['border_lt']};padding:20px;border-radius:10px;margin-bottom:28px;box-shadow:0 1px 4px {P['shadow_sm']}">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <div style="font-size:15px;font-weight:700;color:{P['text']};margin-bottom:3px">{cycle_name}</div>
      <div style="font-size:12px;color:{P['text_sec']}">{sprint} · {start_date} → {end_date}</div>
    </div>
    <span style="background:{status_color};opacity:0.15;color:{status_color};padding:4px 10px;border-radius:5px;font-size:10px;letter-spacing:0.8px;text-transform:uppercase;font-weight:700;border:1px solid {status_color}">{cycle_status}</span>
  </div>
  <div style="display:flex;justify-content:space-between;margin-bottom:8px">
    <div style="font-size:11px;color:{P['muted']};font-weight:600;text-transform:uppercase;letter-spacing:0.5px">Progreso</div>
    <div style="font-size:13px;color:{P['text']};font-weight:700;font-family:DM Mono,monospace">{executed}/{planned} ({progress}%)</div>
  </div>
  <div style="background:{P['surface2']};border-radius:6px;height:6px;overflow:hidden">
    <div style="background:linear-gradient(90deg,{P['accent']},{P['accent_lt']});height:100%;width:{progress}%;border-radius:6px;transition:width 0.3s ease"></div>
  </div>
</div>"""

        flaky_html = "<div class='section-label'>Tests Inestables (Flaky)</div>"
        if flaky:
            for f in flaky[:5]:
                test_id  = f.get("test_id", "N/A")
                flakiness = f.get("flakiness_pct", 0)
                failures  = f.get("failure_count", 0)
                total     = f.get("total_runs", 1)
                fc        = P["crit"] if flakiness > 50 else P["warn"] if flakiness > 30 else P["ok"]
                flaky_html += f"""
<div style="background:{P['surface']};border-left:3px solid {fc};padding:12px 14px;margin-bottom:8px;border-radius:6px">
  <div style="color:{P['text']};font-weight:600;margin-bottom:4px;word-break:break-all;font-family:DM Mono,monospace;font-size:12px">{test_id}</div>
  <div style="color:{P['text_sec']};font-size:13px">Probabilidad de fallo: <span style="color:{fc};font-weight:700">{flakiness:.1f}%</span> · Falló <span style="font-weight:600;font-family:DM Mono,monospace">{failures}/{total}</span> veces</div>
</div>"""
        else:
            flaky_html += f"<p style='color:{P['ok']};font-size:14px;font-weight:600'>✓ Sin tests inestables detectados</p>"

        return estado_html + kpi_html + recent_html + cycle_html + flaky_html

    # ── Trending ──
    def tab_branch_trending(self, days=30):
        df = self._cached("trending", self.queries.get_branch_trending, ttl=120, days=days)
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="SIN DATOS", showarrow=False,
                               font=dict(size=20, color=P["muted"]), x=0.5, y=0.5)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=P["surface2"],
                              height=420, margin=dict(t=50, b=40, l=50, r=20))
            return fig, df

        df["date"] = df["date"].astype(str).str[:10]

        # Paleta Premium PowerBI - Colores audaces con degradados
        BRANCH_COLORS = [
            {"line": "#00d4aa", "fill": "rgba(0, 212, 170, 0.16)", "gradient": "linear-gradient(135deg, rgba(0, 212, 170, 0.25) 0%, rgba(0, 212, 170, 0.05) 100%)"},
            {"line": "#6366f1", "fill": "rgba(99, 102, 241, 0.16)", "gradient": "linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(99, 102, 241, 0.05) 100%)"},
            {"line": "#f59e0b", "fill": "rgba(245, 158, 11, 0.16)", "gradient": "linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(245, 158, 11, 0.05) 100%)"},
            {"line": "#ec4899", "fill": "rgba(236, 72, 153, 0.16)", "gradient": "linear-gradient(135deg, rgba(236, 72, 153, 0.25) 0%, rgba(236, 72, 153, 0.05) 100%)"},
            {"line": "#8b5cf6", "fill": "rgba(139, 92, 246, 0.16)", "gradient": "linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(139, 92, 246, 0.05) 100%)"},
            {"line": "#14b8a6", "fill": "rgba(20, 184, 166, 0.16)", "gradient": "linear-gradient(135deg, rgba(20, 184, 166, 0.25) 0%, rgba(20, 184, 166, 0.05) 100%)"},
        ]

        branches = sorted(df["branch"].unique())
        y_min = max(0,   df["pass_rate"].min() - 8)
        y_max = min(100, df["pass_rate"].max() + 6)

        fig = go.Figure()

        # Línea de referencia 90% con anotación MÁS CLARA
        fig.add_hline(
            y=90, line_dash="solid", line_color=P["crit"], line_width=2.5, opacity=0.55,
            annotation_text="<b style='font-size:12px'>🎯 META: 90%</b>",
            annotation_font_color=P["crit"], annotation_font_size=12,
            annotation_position="right",
            annotation_bgcolor=P["surface"],
            annotation_bordercolor=P["crit"],
            annotation_borderwidth=2,
            annotation_borderpad=6,
        )

        for i, branch in enumerate(branches):
            d = df[df["branch"] == branch].sort_values("date")
            c = BRANCH_COLORS[i % len(BRANCH_COLORS)]

            # Relleno bajo la línea con efecto gradient
            fig.add_trace(go.Scatter(
                x=d["date"], y=d["pass_rate"],
                mode="none", fill="tozeroy",
                fillcolor=c["fill"],
                hoverinfo="skip", showlegend=False,
                name=None,
            ))

            # Línea principal - CON ETIQUETAS en cada punto
            fig.add_trace(go.Scatter(
                x=d["date"], y=d["pass_rate"],
                mode="lines+markers+text", name=f"📊 {branch}",
                line=dict(color=c["line"], width=3.8, shape="spline"),
                marker=dict(
                    size=14, color=c["line"], 
                    line=dict(color=P["bg"], width=3),
                    symbol="circle",
                ),
                text=d["pass_rate"].apply(lambda x: f"{x:.0f}%"),
                textposition="top center",
                textfont=dict(color=c["line"], size=10, family="'DM Mono', monospace", weight=700),
                hovertemplate=(
                    f"<b style='color:{c['line']};font-size:13px'>{branch}</b><br>"
                    "<b>Fecha:</b> %{x}<br>"
                    "<b style='color:#4ade80'>✅ Pass Rate: %{y:.1f}%</b><extra></extra>"
                ),
                opacity=0.95,
            ))

        fig.update_layout(
            title=dict(
                text="<b>📈 TENDENCIA POR RAMA</b><br><sub style='font-weight:400;font-size:12px;color:" + P["text_sec"] + "'>Últimos " + str(days) + " días · Cada punto = un día · Números = % de éxito</sub>",
                font=dict(color=P["text"], size=17, family="'DM Sans', sans-serif"),
                x=0.02, xanchor="left",
            ),
            font=dict(family="'DM Sans', sans-serif", color=P["text_sec"], size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=P["surface2"],
            xaxis=dict(
                type="category", showgrid=True, gridwidth=1, gridcolor="rgba(42, 45, 62, 0.4)",
                zeroline=False,
                color=P["muted"], tickfont=dict(color=P["muted"], size=11),
                linecolor=P["border"], linewidth=1,
                tickangle=-35,
                showline=True,
            ),
            yaxis=dict(
                range=[y_min, y_max],
                showgrid=True, gridwidth=1, gridcolor="rgba(42, 45, 62, 0.4)",
                zeroline=False, color=P["muted"],
                tickfont=dict(color=P["muted"], size=11),
                ticksuffix="%", linecolor=P["border"], linewidth=1,
                showline=True,
            ),
            legend=dict(
                bgcolor="rgba(26,29,39,0.9)", bordercolor=P["accent"], borderwidth=1.5,
                font=dict(size=12, color=P["text_sec"], family="'DM Sans', sans-serif"),
                orientation="v", x=1.01, y=1,
                xanchor="left", yanchor="top",
                itemsizing="constant",
            ),
            hoverlabel=dict(
                bgcolor=P["surface"],
                bordercolor=P["accent"],
                font=dict(size=13, color=P["text"], family="'DM Sans', sans-serif"),
                align="left",
            ),
            margin=dict(t=110, b=90, l=65, r=180),
            height=500,
            hovermode="x unified",
        )

        return fig, df

    # ── Features ──
    def tab_feature_stats(self, days=30):
        features = self._cached("features", self.queries.get_feature_stats, ttl=120, days=days)

        def _empty():
            f = go.Figure()
            f.add_annotation(text="SIN DATOS", showarrow=False,
                             font=dict(size=18, color=P["muted"]), x=0.5, y=0.5)
            f.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=P["surface2"],
                            height=320, margin=dict(t=44, b=16, l=8, r=8))
            return f

        if not features:
            return _empty(), _empty(), pd.DataFrame({"MODULO": ["Sin datos disponibles"]})

        df = pd.DataFrame(features)

        # ── Paleta Power BI style: gradiente por performance ──
        def _bar_color(rate):
            if rate == 100: return "#00d4aa"   # turquesa brillante
            if rate >= 95:  return "#4ade80"   # verde
            if rate >= 90:  return "#4f8ef7"   # azul
            if rate >= 75:  return "#f5a623"   # ámbar
            return "#ff5c5c"                    # rojo

        def _bar_color_dim(rate):
            if rate == 100: return "rgba(0, 212, 170, 0.08)"
            if rate >= 95:  return "rgba(74, 222, 128, 0.08)"
            if rate >= 90:  return "rgba(79, 142, 247, 0.08)"
            if rate >= 75:  return "rgba(245, 166, 35, 0.08)"
            return "rgba(255, 92, 92, 0.08)"

        bar_colors     = [_bar_color(r)     for r in df["pass_rate"]]
        bar_colors_dim = [_bar_color_dim(r) for r in df["pass_rate"]]

        # ── Gráfico 1: Barras de PASS RATE con efecto Premium ──
        fig1 = go.Figure()

        # Barra de fondo (100% en gris muy sutil)
        fig1.add_trace(go.Bar(
            y=df["feature"], x=[100] * len(df),
            orientation="h",
            marker=dict(color=bar_colors_dim, line=dict(width=0)),
            hoverinfo="skip",
            showlegend=False,
            opacity=0.6,
        ))

        # Barra real encima con efecto de brillo
        fig1.add_trace(go.Bar(
            y=df["feature"], x=df["pass_rate"],
            orientation="h",
            marker=dict(
                color=bar_colors,
                line=dict(width=1.5, color=bar_colors),
                opacity=0.92,
            ),
            text=df["pass_rate"].apply(lambda x: f"  {x:.1f}%"),
            textposition="inside",
            textfont=dict(
                color=P["bg"], size=12,
                family="'DM Mono', monospace",
                weight=700,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Pass Rate: <b>%{x:.1f}%</b><br>"
                "<extra></extra>"
            ),
        ))

        fig1.update_layout(
            title=dict(
                text="<b>PASS RATE POR MÓDULO</b>",
                font=dict(color=P["text"], size=15, family="'DM Sans', sans-serif"),
                x=0.02, xanchor="left",
            ),
            font=dict(family="'DM Sans', sans-serif", color=P["text_sec"], size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=P["surface2"],
            barmode="overlay",
            xaxis=dict(
                range=[0, 110],
                showgrid=True, gridwidth=1, gridcolor="rgba(42, 45, 62, 0.3)",
                zeroline=False,
                showticklabels=True,
                tickformat=".0f",
                tickfont=dict(size=10, color=P["muted"]),
                linecolor=P["border"], linewidth=1,
            ),
            yaxis=dict(
                showgrid=False, zeroline=False,
                color=P["text_sec"],
                tickfont=dict(color=P["text_sec"], size=12, family="'DM Sans', sans-serif"),
                linecolor="rgba(0,0,0,0)",
                ticklabelposition="outside left",
            ),
            hoverlabel=dict(
                bgcolor=P["surface"], bordercolor=P["accent"],
                font=dict(size=12, color=P["text"]),
            ),
            margin=dict(t=60, b=20, l=240, r=30),
            height=max(280, len(df) * 68 + 100),
            bargap=0.32,
            showlegend=False,
        )

        # ── Gráfico 2: CASOS FALLIDOS - Barras horizontales ULTRA CLARAS ──
        df_fails = df.sort_values("failed", ascending=True).tail(8)  # Top 8 con más fallos
        
        fig2 = go.Figure()

        # Determinar color por cantidad de fallos
        fail_colors = []
        for failed in df_fails["failed"]:
            if failed == 0:
                fail_colors.append(P["ok"])          # Verde si no hay fallos
            elif failed <= 5:
                fail_colors.append(P["warn"])        # Amarillo si hay pocos fallos
            else:
                fail_colors.append(P["crit"])        # Rojo si hay muchos fallos

        # Barra principal - CASOS FALLIDOS (prominente)
        fig2.add_trace(go.Bar(
            y=df_fails["feature"],
            x=df_fails["failed"],
            orientation="h",
            marker=dict(
                color=fail_colors,
                line=dict(width=2, color=[c for c in fail_colors]),
                opacity=0.88,
            ),
            text=df_fails["failed"].apply(lambda x: f"  ❌ {int(x)} FALLOS"),
            textposition="inside",
            textfont=dict(
                color=P["bg"],
                size=12,
                family="'DM Mono', monospace",
                weight=700,
            ),
            name="Tests Fallidos",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "<b style='color:#ff5c5c'>❌ FALLOS: %{x}</b><br>"
                "<extra></extra>"
            ),
        ))

        # Barra de fondo (TESTS PASADOS en gris sutil)
        fig2.add_trace(go.Bar(
            y=df_fails["feature"],
            x=df_fails["passed"],
            orientation="h",
            marker=dict(
                color="rgba(74, 222, 128, 0.2)",
                line=dict(width=0),
            ),
            text=df_fails["passed"].apply(lambda x: f"  ✅ {int(x)}"),
            textposition="inside",
            textfont=dict(
                color=P["muted"],
                size=11,
                family="'DM Mono', monospace",
            ),
            name="Tests Pasados",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "<b style='color:#4ade80'>✅ PASADOS: %{x}</b><br>"
                "<extra></extra>"
            ),
        ))

        fig2.update_layout(
            title=dict(
                text="<b>⚠️ MÓDULOS CON FALLOS CRÍTICOS</b><br><sub style='font-weight:400;font-size:12px;color:" + P["text_sec"] + "'>Rojo = Alto riesgo · Amarillo = Medio riesgo · Verde = Sin fallos</sub>",
                font=dict(color=P["text"], size=15, family="'DM Sans', sans-serif"),
                x=0.02, xanchor="left",
            ),
            font=dict(family="'DM Sans', sans-serif", color=P["text_sec"], size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=P["surface2"],
            barmode="stack",
            xaxis=dict(
                showgrid=True, gridwidth=1, gridcolor="rgba(42, 45, 62, 0.3)",
                zeroline=False,
                tickfont=dict(size=10, color=P["muted"]),
                linecolor=P["border"], linewidth=1,
            ),
            yaxis=dict(
                showgrid=False, zeroline=False,
                color=P["text_sec"],
                tickfont=dict(color=P["text_sec"], size=12, family="'DM Sans', sans-serif"),
                linecolor="rgba(0,0,0,0)",
            ),
            legend=dict(
                bgcolor="rgba(26,29,39,0.85)", bordercolor=P["border"], borderwidth=1,
                font=dict(size=11, color=P["text_sec"], family="'DM Sans', sans-serif"),
                orientation="h",
                x=0.5, y=1.15,
                xanchor="center", yanchor="top",
            ),
            hoverlabel=dict(
                bgcolor=P["surface"],
                bordercolor=P["crit"],
                font=dict(size=13, color=P["text"], family="'DM Mono', monospace"),
            ),
            margin=dict(t=100, b=40, l=280, r=30),
            height=max(300, len(df_fails) * 65 + 120),
            showlegend=True,
        )

        # ── Tabla ──
        df_disp = df[["feature", "total_tests", "passed", "failed", "pass_rate"]].copy()
        df_disp.columns = ["MÓDULO", "TOTAL", "OK", "FAIL", "PASS RATE %"]
        return fig1, fig2, df_disp

    # ── Flaky ──
    def tab_flaky_tests(self, days=30):
        flaky = self._cached("flaky", self.queries.get_flaky_tests, ttl=120, days=days, limit=20)
        if not flaky:
            return pd.DataFrame({"ESTADO": ["Sin flaky tests detectados"]})
        for f in flaky:
            fecha_str = f.get("last_run_date", "N/A")
            if fecha_str != "N/A":
                try:
                    from datetime import datetime as dt_class
                    dt_obj = dt_class.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    if dt_obj.tzinfo is None:
                        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                    f["last_run_date"] = dt_obj.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                except:
                    f["last_run_date"] = fecha_str[:19].replace("T", " ")
        df = pd.DataFrame(flaky)
        df.columns = ["TEST ID","FLAKINESS %","FALLOS","TOTAL RUNS","ULTIMO RUN"]
        return df

    # ── Riesgo IA ──
    def tab_ai_risk(self, days=30):
        blockers = self._cached("blockers", self.queries.get_ai_blockers, ttl=120, days=days, limit=10)
        if not blockers:
            return f"<div class='section-label'>RIESGO IA</div><p style='color:{P['ok']};font-size:14px;font-weight:600'>✓ Sin blockers críticos activos</p>"
        cards = []
        for b in blockers:
            pr   = b.get("pr_number","N/A")
            rama = b.get("branch","unknown")
            risk = b.get("overall_risk_level","LOW")
            text = b.get("ai_blockers","—")
            fecha_str = b.get("run_date","N/A")
            fecha = fecha_str[:19].replace("T"," ")
            try:
                from datetime import datetime as dt_class
                dt_obj = dt_class.fromisoformat(fecha_str.replace("Z", "+00:00"))
                if dt_obj.tzinfo is None:
                    dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                fecha = dt_obj.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            rc = {"CRITICAL":"crit","MEDIUM":"warn","LOW":"ok"}.get(risk,"ok")
            cc = {"CRITICAL":"critical","MEDIUM":"medium","LOW":"low"}.get(risk,"low")
            cards.append(f"""
<div class="risk-card {cc}">
  <div class="risk-meta">PR #{pr} &nbsp;·&nbsp; {rama} &nbsp;·&nbsp; {fecha}</div>
  <div style="margin-bottom:8px"><span class="badge {rc}">{risk}</span></div>
  <div class="risk-body">{text}</div>
</div>""")
        return f"<div class='section-label'>Análisis de Riesgos IA</div>" + "".join(cards)

    # ── Timeline ──
    def tab_timeline(self, days=30):
        df = self._cached("timeline", self.queries.get_daily_pass_rate, ttl=120, days=days)
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="SIN DATOS", showarrow=False,
                               font=dict(size=20, color=P["muted"]), x=0.5, y=0.5)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=P["surface2"],
                              height=420, margin=dict(t=50, b=40, l=50, r=20))
            return fig, df

        df["date"]      = df["date"].astype(str).str[:10]
        df["fail_rate"] = (100 - df["pass_rate"]).round(2)

        fig = go.Figure()

        # ── Área FAIL sutil debajo (gradiente rojo) ──
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["fail_rate"],
            mode="none", fill="tozeroy",
            fillcolor="rgba(255, 92, 92, 0.18)",
            hoverinfo="skip", showlegend=False,
        ))

        # ── Área PASS verde dominante con gradiente ──
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["pass_rate"],
            mode="none", fill="tozeroy",
            fillcolor="rgba(0, 212, 170, 0.15)",
            hoverinfo="skip", showlegend=False,
        ))

        # ── Línea PASS principal - grosor Premium ──
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["pass_rate"],
            mode="lines+markers", name="✅ Pass Rate",
            line=dict(color="#00d4aa", width=3.5, shape="spline"),
            marker=dict(
                size=10,
                color=[_risk_color(r) for r in df["risk_level"]],
                line=dict(color=P["bg"], width=2.5),
                symbol="circle",
            ),
            hovertemplate="<b>%{x}</b><br>✅ Pass: <b>%{y:.1f}%</b><extra></extra>",
            opacity=0.95,
        ))

        # ── Línea FAIL fina y punteada ──
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["fail_rate"],
            mode="lines+markers", name="❌ Fail Rate",
            line=dict(color=P["crit"], width=2, shape="spline", dash="dot"),
            marker=dict(
                size=8,
                color=P["crit"],
                line=dict(color=P["bg"], width=1.5),
                symbol="diamond",
            ),
            hovertemplate="<b>%{x}</b><br>❌ Fail: <b>%{y:.1f}%</b><extra></extra>",
            opacity=0.85,
        ))

        # ── Línea objetivo 90% - Premium design ──
        fig.add_hline(
            y=90, line_dash="dash", line_color=P["warn"], line_width=2.5, opacity=0.5,
            annotation_text="<b>META: 90%</b>",
            annotation_font_color=P["warn"], annotation_font_size=11,
            annotation_position="right",
            annotation_bgcolor="rgba(245, 166, 35, 0.1)",
            annotation_bordercolor=P["warn"],
            annotation_borderwidth=1.5,
            annotation_borderpad=5,
        )

        # ── Anotación último valor con indicador de tendencia ──
        if len(df) > 0:
            last = df.iloc[-1]
            last_color = _risk_color(last["risk_level"])
            
            # Calcular tendencia
            if len(df) > 1:
                prev = df.iloc[-2]
                tendencia = last["pass_rate"] - prev["pass_rate"]
                if tendencia > 0:
                    emoji_tend = "📈"
                    color_tend = P["ok"]
                elif tendencia < 0:
                    emoji_tend = "📉"
                    color_tend = P["crit"]
                else:
                    emoji_tend = "➡️"
                    color_tend = P["warn"]
                tend_text = f"{emoji_tend} {abs(tendencia):.1f}%"
            else:
                tend_text = "Inicio"
                color_tend = P["text_sec"]

            fig.add_annotation(
                x=last["date"], y=last["pass_rate"],
                text=f"<b>{last['pass_rate']:.1f}%</b><br><sub>{tend_text}</sub>",
                showarrow=True, arrowhead=2,
                arrowcolor=last_color, arrowwidth=2.5, arrowsize=1.5,
                ax=40, ay=-40,
                font=dict(color=last_color, size=12, family="'DM Mono', monospace"),
                bgcolor=P["surface"], bordercolor=last_color,
                borderwidth=2, borderpad=8,
            )

        fig.update_layout(
            title=dict(
                text="<b>EVOLUCIÓN DIARIA DE CALIDAD</b><br><sub style='font-weight:400;font-size:12px;color:" + P["text_sec"] + "'>Últimos " + str(days) + " días</sub>",
                font=dict(color=P["text"], size=16, family="'DM Sans', sans-serif"),
                x=0.02, xanchor="left",
            ),
            font=dict(family="'DM Sans', sans-serif", color=P["text_sec"], size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=P["surface2"],
            xaxis=dict(
                type="category", showgrid=True, gridwidth=1, gridcolor="rgba(42, 45, 62, 0.4)",
                zeroline=False,
                color=P["muted"], tickfont=dict(color=P["muted"], size=11),
                linecolor=P["border"], linewidth=1,
                tickangle=-35,
                showline=True,
            ),
            yaxis=dict(
                range=[0, 105],
                showgrid=True, gridwidth=1, gridcolor="rgba(42, 45, 62, 0.4)",
                zeroline=False, color=P["muted"],
                tickfont=dict(color=P["muted"], size=11),
                ticksuffix="%", linecolor=P["border"], linewidth=1,
                showline=True,
            ),
            legend=dict(
                bgcolor="rgba(26,29,39,0.85)", bordercolor=P["accent"], borderwidth=1.5,
                font=dict(size=12, color=P["text_sec"], family="'DM Sans', sans-serif"),
                orientation="h", x=0.5, y=1.12,
                xanchor="center", yanchor="top",
            ),
            hoverlabel=dict(
                bgcolor=P["surface"], bordercolor=P["accent"],
                font=dict(size=12, color=P["text"]),
            ),
            margin=dict(t=100, b=80, l=60, r=80),
            height=480, hovermode="x unified",
        )
        return fig, df


# ─────────────────────────────────────────────
# Gradio App
# ─────────────────────────────────────────────
def create_gradio_app(queries: DashboardQueries) -> gr.Blocks:
    ui = DashboardUI(queries)

    with gr.Blocks(fill_height=True, title="Agent Karate Dashboard") as app:
        gr.Markdown(f"""
<div class="header">
  <div>
    <div style="font-size:26px;font-family:'DM Sans',sans-serif;font-weight:700;color:{P['text']};letter-spacing:-0.8px">agent karate</div>
    <div style="font-size:11px;letter-spacing:1px;color:{P['muted']};margin-top:4px;text-transform:uppercase;font-weight:500">quality metrics dashboard</div>
  </div>
  <div style="color:{P['muted']};font-size:12px">Powered by MongoDB + Karate + AI</div>
</div>""")

        global_days = gr.Radio([7, 14, 30, 60, 90], value=30, label="Rango de días")

        with gr.Tabs():
            with gr.TabItem("Overview"):
                overview_html = gr.HTML(value="Cargando...")
                global_days.change(lambda d: ui.tab_overview(int(d)),   inputs=global_days, outputs=overview_html)
                app.load(lambda: ui.tab_overview(30), outputs=overview_html)

            with gr.TabItem("Trending"):
                chart_tr = gr.Plot()
                table_tr = gr.Dataframe(interactive=False)
                global_days.change(lambda d: ui.tab_branch_trending(int(d)), inputs=global_days, outputs=[chart_tr, table_tr])
                app.load(lambda: ui.tab_branch_trending(30), outputs=[chart_tr, table_tr])

            with gr.TabItem("Por Módulo"):
                chart1_mod = gr.Plot()
                chart2_mod = gr.Plot()
                table_mod  = gr.Dataframe(interactive=False)
                global_days.change(lambda d: ui.tab_feature_stats(int(d)), inputs=global_days, outputs=[chart1_mod, chart2_mod, table_mod])
                app.load(lambda: ui.tab_feature_stats(30), outputs=[chart1_mod, chart2_mod, table_mod])

            with gr.TabItem("Flaky Tests"):
                table_fl = gr.Dataframe(interactive=False)
                global_days.change(lambda d: ui.tab_flaky_tests(int(d)), inputs=global_days, outputs=table_fl)
                app.load(lambda: ui.tab_flaky_tests(30), outputs=table_fl)

            with gr.TabItem("Riesgo IA"):
                risk_html = gr.HTML(value="Cargando...")
                global_days.change(lambda d: ui.tab_ai_risk(int(d)), inputs=global_days, outputs=risk_html)
                app.load(lambda: ui.tab_ai_risk(30), outputs=risk_html)

            with gr.TabItem("Timeline"):
                chart_tl = gr.Plot()
                table_tl = gr.Dataframe(interactive=False)
                global_days.change(lambda d: ui.tab_timeline(int(d)), inputs=global_days, outputs=[chart_tl, table_tl])
                app.load(lambda: ui.tab_timeline(30), outputs=[chart_tl, table_tl])

    return app


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    """Main entry point"""
    print("[Agent Karate Dashboard]")
    print("Initializing MongoDB connection...")

    try:
        sync    = MongoSync()
        queries = DashboardQueries(sync)
        app     = create_gradio_app(queries)

        port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
        print(f"Starting dashboard on http://localhost:{port}")
        print("Press Ctrl+C to stop")

        app.launch(
            server_name="0.0.0.0",
            server_port=port,
            show_error=True,
            quiet=False,
            css=CSS,
        )
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        raise


if __name__ == "__main__":
    main()