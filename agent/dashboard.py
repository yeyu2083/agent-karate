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


# -- Design Tokens --
P = {
    "bg":       "#0c0e14",
    "surface":  "#13151f",
    "surface2": "#1a1d2e",
    "border":   "#252836",
    "border2":  "#2f3347",
    "text":     "#e2e4ef",
    "muted":    "#565b78",
    "accent":   "#818cf8",
    "accent2":  "#38bdf8",
    "ok":       "#34d399",
    "warn":     "#fbbf24",
    "crit":     "#f87171",
    "ok_bg":    "#34d39918",
    "warn_bg":  "#fbbf2418",
    "crit_bg":  "#f8717118",
}

PLOT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'DM Mono', monospace", color=P["muted"], size=13),
    title_font=dict(family="'DM Mono', monospace", color=P["text"], size=14),
    xaxis=dict(showgrid=False, zeroline=False, color=P["muted"],
               tickfont=dict(size=12), linecolor=P["border"]),
    yaxis=dict(showgrid=True, gridcolor=P["border"], zeroline=False,
               color=P["muted"], tickfont=dict(size=12)),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=P["border"], borderwidth=1,
                font=dict(size=12, color=P["muted"])),
    hoverlabel=dict(bgcolor=P["surface2"], bordercolor=P["border2"],
                    font=dict(family="'DM Mono', monospace", size=13, color=P["text"])),
    margin=dict(t=44, b=28, l=12, r=12),
)

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@300;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}
body, .gradio-container {{ background:{P['bg']} !important; color:{P['text']} !important; font-family:'DM Mono',monospace !important; }}

/* Header */
.dash-header {{ padding:36px 0 28px; border-bottom:1px solid {P['border']}; margin-bottom:28px; }}
.dash-title {{ font-family:'Syne',sans-serif !important; font-size:28px !important; font-weight:700 !important; color:{P['text']} !important; letter-spacing:-0.5px; margin:0 !important; }}
.dash-sub {{ font-size:12px !important; color:{P['muted']} !important; letter-spacing:3px; text-transform:uppercase; margin-top:6px !important; }}

/* Tabs */
.tab-nav {{ background:transparent !important; border-bottom:1px solid {P['border']} !important; gap:0 !important; padding:0 !important; }}
.tab-nav button {{ font-family:'DM Mono',monospace !important; font-size:12px !important; font-weight:500 !important; letter-spacing:2px !important; text-transform:uppercase !important; color:{P['muted']} !important; background:transparent !important; border:none !important; border-bottom:2px solid transparent !important; padding:12px 20px !important; border-radius:0 !important; transition:all .2s !important; }}
.tab-nav button:hover {{ color:{P['text']} !important; }}
.tab-nav button.selected {{ color:{P['accent']} !important; border-bottom:2px solid {P['accent']} !important; }}
.tabitem {{ background:transparent !important; border:none !important; padding:24px 0 0 !important; }}

/* KPI Grid */
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; margin-bottom:28px; }}
.kpi-card {{ background:{P['surface']} !important; border:1px solid {P['border']} !important; border-radius:10px !important; padding:18px !important; }}
.kpi-label {{ font-size:11px !important; letter-spacing:2.5px !important; text-transform:uppercase !important; color:{P['muted']} !important; margin-bottom:8px; }}
.kpi-value {{ font-family:'Syne',sans-serif !important; font-size:36px !important; font-weight:300 !important; line-height:1; }}
.kpi-value.ok   {{ color:{P['ok']}   !important; }}
.kpi-value.warn {{ color:{P['warn']} !important; }}
.kpi-value.crit {{ color:{P['crit']} !important; }}
.kpi-value.base {{ color:{P['accent']} !important; }}

/* Risk cards */
.risk-card {{ background:{P['surface']}; border:1px solid {P['border']}; border-radius:10px; padding:16px 18px; margin-bottom:12px; }}
.risk-card.critical {{ border-left:3px solid {P['crit']}; }}
.risk-card.medium   {{ border-left:3px solid {P['warn']}; }}
.risk-card.low      {{ border-left:3px solid {P['ok']};  }}
.risk-meta {{ font-size:12px; letter-spacing:1px; text-transform:uppercase; color:{P['muted']}; margin-bottom:8px; }}
.risk-body {{ font-size:14px; color:{P['text']}; line-height:1.6; }}
.badge {{ display:inline-block; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; font-weight:600; padding:2px 8px; border-radius:4px; }}
.badge.ok   {{ background:{P['ok_bg']};   color:{P['ok']};   }}
.badge.warn {{ background:{P['warn_bg']}; color:{P['warn']}; }}
.badge.crit {{ background:{P['crit_bg']}; color:{P['crit']}; }}

/* Controls */
.refresh-btn {{ font-family:'DM Mono',monospace !important; font-size:13px !important; letter-spacing:1px !important; background:transparent !important; border:1px solid {P['border2']} !important; color:{P['muted']} !important; border-radius:6px !important; transition:all .2s !important; }}
.refresh-btn:hover {{ border-color:{P['accent']} !important; color:{P['accent']} !important; }}
.status-box textarea {{ font-family:'DM Mono',monospace !important; font-size:13px !important; background:{P['surface']} !important; color:{P['muted']} !important; border:1px solid {P['border']} !important; border-radius:6px !important; }}

/* Radio/Range inputs */
input[type="radio"], input[type="range"] {{ accent-color: {P['accent']} !important; }}
.gradio-radio {{ color: {P['text']} !important; opacity: 1 !important; }}
.gradio-radio label {{ color: {P['text']} !important; font-size:14px !important; }}
label {{ color: {P['text']} !important; opacity: 1 !important; font-weight: 500 !important; }}

/* Suprimir focus outlines de Gradio */
*:focus {{ outline: none !important; box-shadow: none !important; }}
input:focus, button:focus, textarea:focus {{ outline: none !important; box-shadow: none !important; border-color: {P['border2']} !important; }}
.gradio-container *:focus {{ outline: none !important; box-shadow: none !important; }}

/* Tables */
.dataframe th {{ background:{P['surface2']} !important; color:{P['muted']} !important; font-size:11px !important; letter-spacing:2px !important; text-transform:uppercase !important; padding:10px 14px !important; border-bottom:1px solid {P['border2']} !important; }}
.dataframe td {{ background:{P['surface']} !important; color:{P['text']} !important; padding:9px 14px !important; border-bottom:1px solid {P['border']} !important; font-size:14px !important; }}
.dataframe tr:hover td {{ background:{P['surface2']} !important; }}

/* Plot wrapper */
.plot-container {{ background:{P['surface']} !important; border:1px solid {P['border']} !important; border-radius:10px !important; overflow:hidden !important; }}

/* Section label */
.section-label {{ font-size:12px; letter-spacing:3px; text-transform:uppercase; color:{P['muted']}; margin-bottom:16px; padding-bottom:10px; border-bottom:1px solid {P['border']}; }}

footer, .show-api {{ display:none !important; }}
"""


def _layout(**kw):
    return {**PLOT_BASE, **kw}

def _risk_color(r):
    return {"CRITICAL": P["crit"], "MEDIUM": P["warn"], "LOW": P["ok"]}.get(r, P["muted"])


# -- DashboardQueries --

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
            for doc in results:
                doc["_id"] = str(doc["_id"])
                doc["run_date"] = doc["run_date"].isoformat()
                # Asegurar que branch tenga un valor legible
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
            if r:
                d = r[0]; rate = d["avg_pass_rate"]
                risk = "LOW" if rate == 100 else "MEDIUM" if rate >= 90 else "CRITICAL"
                return {"total_tests": int(d["total_tests"]), "passed_tests": int(d["passed_tests"]),
                        "failed_tests": int(d["failed_tests"]), "overall_pass_rate": round(rate, 2),
                        "overall_risk_level": risk, "critical_runs": int(d["critical_count"])}
            return {"total_tests":0,"passed_tests":0,"failed_tests":0,"overall_pass_rate":0,
                    "overall_risk_level":"UNKNOWN","critical_runs":0}
        except Exception as e:
            print(f"Error get_kpis_summary: {e}"); return {}

    def get_branch_trending(self, days=30, limit_branches=5):
        try:
            start = datetime.now(timezone.utc) - timedelta(days=days)
            col = self.db["execution_summaries"]
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


# -- DashboardUI --

class DashboardUI:
    def __init__(self, queries):
        self.queries = queries
        self._ct, self._cd = {}, {}

    def _cached(self, key, fn, ttl=60, **kw):
        now = datetime.now(timezone.utc)
        # Crear clave única con parámetros
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
            return [] if isinstance(fn.__name__, str) and "list" in fn.__name__ else pd.DataFrame()

    def refresh_cache(self):
        self._ct.clear(); self._cd.clear()

    # Overview
    def tab_overview(self, days=30):
        from datetime import datetime as dt_class
        
        kpis       = self._cached("kpis",      self.queries.get_kpis_summary,      days=days)
        last_execs = self._cached("last_exec", self.queries.get_latest_executions,  limit=5, days=days)
        blockers   = self._cached("blockers",  self.queries.get_ai_blockers,        ttl=120, days=days, limit=3)
        cycle      = self._cached("cycle",     self.queries.get_current_cycle,      ttl=300)
        flaky      = self._cached("flaky_ov",  self.queries.get_flaky_tests,        ttl=120, days=days, limit=5)

        # === 1. ESTADO SISTEMA ===
        # Calcular estado basado en último run + blockers
        last_run = last_execs[0] if last_execs else None
        last_pass_rate = last_run.get("overall_pass_rate", 100) if last_run else 100
        
        # Calcular tiempo desde último run
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
                
                # Asegurar que run_dt sea offset-aware
                if run_dt.tzinfo is None:
                    run_dt = run_dt.replace(tzinfo=timezone.utc)
                    
                now = datetime.now(timezone.utc)
                delta = now - run_dt
                mins = int(delta.total_seconds() / 60)
                if mins < 60:
                    time_since_last = f"hace {mins} min"
                elif mins < 1440:
                    hours = mins // 60
                    time_since_last = f"hace {hours} h"
                else:
                    days_ago = mins // 1440
                    time_since_last = f"hace {days_ago} d"
            except Exception as te:
                print(f"Error parsing time: {te}")
                time_since_last = "N/A"
        
        # Determinar estado: BLOQUEADO / ATENCIÓN / SALUDABLE
        has_critical_blockers = any(b.get("overall_risk_level") == "CRITICAL" for b in blockers)
        last_exec_old = False
        if last_run:
            try:
                run_dt = dt_class.fromisoformat(str(last_run["run_date"]).replace("Z", "+00:00"))
                if run_dt.tzinfo is None:
                    run_dt = run_dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                hours_since = (now - run_dt).total_seconds() / 3600
                last_exec_old = hours_since > 24
            except:
                pass
        
        if last_pass_rate < 70 or has_critical_blockers:
            estado = "BLOQUEADO"
            estado_color = P["crit"]
            estado_bg = "rgba(248, 113, 113, 0.1)"
        elif last_pass_rate < 90 or last_exec_old:
            estado = "ATENCIÓN REQUERIDA"
            estado_color = P["warn"]
            estado_bg = "rgba(251, 191, 36, 0.1)"
        else:
            estado = "SISTEMA SALUDABLE"
            estado_color = P["ok"]
            estado_bg = "rgba(52, 211, 153, 0.1)"
            
        lr_total = last_run.get("total_tests", 0) if last_run else 0
        lr_passed = last_run.get("passed_tests", 0) if last_run else 0
        lr_failed = last_run.get("failed_tests", 0) if last_run else 0
        
        estado_html = f"""
<div style="background:{estado_bg};border:1px solid {estado_color};border-radius:10px;padding:20px;margin-bottom:28px;display:flex;align-items:center;justify-content:space-between">
  <div style="flex:1">
    <div style="font-size:14px;letter-spacing:2.5px;text-transform:uppercase;color:{P['muted']};margin-bottom:6px">ESTADO ACTUAL DEL SISTEMA • {time_since_last}</div>
    <div style="font-size:42px;font-weight:700;color:{estado_color};font-family:'Syne',sans-serif;letter-spacing:-1px">{estado}</div>
  </div>
  <div style="display:flex;gap:32px;text-align:right;padding-left:32px;border-left:1px solid {estado_color}33">
    <div>
      <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:{P['muted']}">Total Tests</div>
      <div style="font-size:28px;color:{P['text']};font-weight:600;margin-top:2px;font-family:'Syne',sans-serif">{lr_total}</div>
    </div>
    <div>
      <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:{P['muted']}">Pasaron (OK)</div>
      <div style="font-size:28px;color:{P['ok']};font-weight:600;margin-top:2px;font-family:'Syne',sans-serif">{lr_passed}</div>
    </div>
    <div>
      <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:{P['muted']}">Fallaron (ERROR)</div>
      <div style="font-size:28px;color:{P['crit']};font-weight:600;margin-top:2px;font-family:'Syne',sans-serif">{lr_failed}</div>
    </div>
    <div>
      <div style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:{P['muted']}">% Éxito</div>
      <div style="font-size:28px;color:{estado_color};font-weight:600;margin-top:2px;font-family:'Syne',sans-serif">{last_pass_rate}%</div>
    </div>
  </div>
</div>"""

        # === 2. KPIs PRINCIPALES ===
        rate  = kpis.get("overall_pass_rate", 0)
        risk  = kpis.get("overall_risk_level", "UNKNOWN")
        rc    = "ok" if rate == 100 else "warn" if rate >= 90 else "crit"
        riskc = "ok" if risk == "LOW" else "warn" if risk == "MEDIUM" else "crit"

        kpi_html = f"""
<div class="section-label">MÉTRICAS ACUMULADAS (Últimos {days} días)</div>
<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-label">TOTAL TESTS EJECUTADOS</div><div class="kpi-value base">{kpis.get('total_tests',0)}</div></div>
  <div class="kpi-card"><div class="kpi-label">TESTS QUE PASARON (OK)</div><div class="kpi-value ok">{kpis.get('passed_tests',0)}</div></div>
  <div class="kpi-card"><div class="kpi-label">TESTS QUE FALLARON (ERROR)</div><div class="kpi-value crit">{kpis.get('failed_tests',0)}</div></div>
  <div class="kpi-card"><div class="kpi-label">% DE ÉXITO PROMEDIO</div><div class="kpi-value {rc}">{rate}%</div></div>
  <div class="kpi-card"><div class="kpi-label">NIVEL DE RIESGO GLOBAL</div><div class="kpi-value {riskc}">{risk}</div></div>
  <div class="kpi-card"><div class="kpi-label">EJECUCIONES CRÍTICAS</div><div class="kpi-value warn">{kpis.get('critical_runs',0)}</div></div>
</div>"""

        # === 3. ÚLTIMAS EJECUCIONES (resumidas) ===
        recent_html = "<div class='section-label' style='margin-top:24px'>HISTORIAL DE ÚLTIMAS EJECUCIONES</div>"
        if last_execs:
            recent_rows = "<table style='width:100%;border-collapse:collapse;margin-bottom:24px'>"
            recent_rows += f"<tr style='background:{P['surface2']};border-bottom:1px solid {P['border2']}'>"
            for header in ["RAMA / PR", "% DE ÉXITO", "NIVEL DE RIESGO", "EJECUTADO HACE"]:
                recent_rows += f"<th style='padding:10px 12px;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:{P['muted']};text-align:left'>{header}</th>"
            recent_rows += "</tr>"
            
            for ex in last_execs[:5]:
                branch = ex.get("branch", "N/A")
                pass_rate = round(float(ex.get("overall_pass_rate", 0)), 1)
                risk = ex.get("overall_risk_level", "LOW")
                run_date = ex.get("run_date", "N/A")
                
                # Tiempo relativo
                time_rel = "N/A"
                try:
                    run_date_str = str(run_date)
                    if "T" in run_date_str:
                        run_date_str = run_date_str.split(".")[0] if "." in run_date_str else run_date_str
                        run_date_str = run_date_str.replace("Z", "+00:00")
                        run_dt = dt_class.fromisoformat(run_date_str)
                    else:
                        run_dt = dt_class.fromisoformat(run_date_str)
                        
                    # Asegurar que run_dt sea offset-aware
                    if run_dt.tzinfo is None:
                        run_dt = run_dt.replace(tzinfo=timezone.utc)
                        
                    now = datetime.now(timezone.utc)
                    delta = now - run_dt
                    mins = int(delta.total_seconds() / 60)
                    if mins < 60:
                        time_rel = f"{mins} min"
                    elif mins < 1440:
                        hours = mins // 60
                        time_rel = f"{hours} h"
                    else:
                        days_ago = mins // 1440
                        time_rel = f"{days_ago} d"
                except Exception as e:
                    print(f"Error calc time_rel: {e}")
                
                # Color riesgo
                risk_color = P["ok"] if risk == "LOW" else P["warn"] if risk == "MEDIUM" else P["crit"]
                risk_bg = P["ok_bg"] if risk == "LOW" else P["warn_bg"] if risk == "MEDIUM" else P["crit_bg"]
                
                recent_rows += f"""<tr style='border-bottom:1px solid {P['border']};background:{P['surface']}'>
                    <td style='padding:9px 12px;font-size:13px;color:{P['text']}'>{branch}</td>
                    <td style='padding:9px 12px;font-size:13px;color:{P['text']};font-weight:500'>{pass_rate}%</td>
                    <td style='padding:9px 12px;font-size:12px'><span style='background:{risk_bg};color:{risk_color};padding:3px 8px;border-radius:4px;letter-spacing:1px;text-transform:uppercase;font-weight:600'>{risk}</span></td>
                    <td style='padding:9px 12px;font-size:13px;color:{P['muted']}'>{time_rel}</td>
                </tr>"""
            
            recent_rows += "</table>"
            recent_html += recent_rows
        else:
            recent_html += f"<p style='color:{P['muted']};font-size:14px'>Sin ejecuciones</p>"

        # === 4. CICLO ACTUAL ===
        cycle_html = ""
        if cycle:
            cycle_name = cycle.get("cycle_name", "Unknown")
            sprint = cycle.get("sprint", "N/A")
            start_date = cycle.get("start_date", "N/A")[:10] if cycle.get("start_date") else "N/A"
            end_date = cycle.get("end_date", "N/A")[:10] if cycle.get("end_date") else "N/A"
            planned = cycle.get("total_tests_planned", 0)
            executed = cycle.get("tests_executed", 0)
            progress = round(executed/planned*100) if planned > 0 else 0
            cycle_status = cycle.get("status", "Unknown")
            status_color = P["ok"] if cycle_status == "Active" else P["warn"] if cycle_status == "In Progress" else P["muted"]
            
            cycle_html = f"""
<div class="section-label" style="margin-top:24px">CICLO ACTUAL</div>
<div style="background:{P['surface']};border:1px solid {P['border']};padding:16px;border-radius:10px;margin-bottom:24px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
    <div style="flex:1">
      <div style="font-size:16px;font-weight:500;color:{P['text']};margin-bottom:4px">{cycle_name}</div>
      <div style="font-size:13px;color:{P['muted']}">{sprint} • {start_date} → {end_date}</div>
    </div>
    <div style="background:{status_color}22;color:{status_color};padding:4px 10px;border-radius:4px;font-size:12px;letter-spacing:1px;text-transform:uppercase;font-weight:600">{cycle_status}</div>
  </div>
  <div style="margin-bottom:8px">
    <div style="display:flex;justify-content:space-between;margin-bottom:4px">
      <div style="font-size:13px;color:{P['muted']}">Progreso</div>
      <div style="font-size:13px;color:{P['text']};font-weight:500">{executed}/{planned} ({progress}%)</div>
    </div>
    <div style="background:{P['surface2']};border-radius:4px;height:6px;overflow:hidden">
      <div style="background:{P['accent']};height:100%;width:{progress}%;transition:width 0.3s"></div>
    </div>
  </div>
</div>"""

        # === 5. FLAKY TESTS ===
        flaky_html = "<div class='section-label'>TESTS INESTABLES (FLAKY TESTS)</div>"
        if flaky:
            flaky_list_html = ""
            for f in flaky[:5]:
                test_id = f.get("test_id", "N/A")
                flakiness = f.get("flakiness_pct", 0)
                failures = f.get("failure_count", 0)
                total = f.get("total_runs", 1)
                flakiness_color = "crit" if flakiness > 50 else "warn" if flakiness > 30 else "ok"
                flaky_list_html += f"""
<div style="background:{P['surface']};border-left:3px solid {_risk_color({'crit':'CRITICAL','warn':'MEDIUM','ok':'LOW'}.get(flakiness_color,'LOW'))};padding:12px;margin-bottom:8px;border-radius:6px;font-size:14px">
  <div style="color:{P['text']};font-weight:500;margin-bottom:4px;word-break:break-all">{test_id}</div>
  <div style="color:{P['muted']};font-size:13px">Probabilidad de fallo: <span style="color:{_risk_color({'crit':'CRITICAL','warn':'MEDIUM','ok':'LOW'}.get(flakiness_color,'LOW'))}">{flakiness:.1f}%</span> • Falló {failures} veces de {total} ejecuciones</div>
</div>"""
            flaky_html += flaky_list_html
        else:
            flaky_html += f"<p style='color:{P['ok']};font-size:15px'>No se detectaron tests inestables</p>"

        html_content = estado_html + kpi_html + recent_html + cycle_html + flaky_html
        return html_content

    # Trending
    def tab_branch_trending(self, days=30):
        df = self._cached("trending", self.queries.get_branch_trending, ttl=120, days=days)
        if df.empty: return go.Figure(), df
        colors = [P["accent"], P["accent2"], P["ok"], P["warn"], P["crit"]]
        fig = go.Figure()
        for i, branch in enumerate(df["branch"].unique()):
            d = df[df["branch"] == branch]; c = colors[i % len(colors)]
            fig.add_trace(go.Scatter(
                x=d["date"], y=d["pass_rate"], mode="lines+markers", name=branch,
                line=dict(color=c, width=2, shape="spline"),
                marker=dict(size=5, color=c),
                hovertemplate=f"<b>{branch}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
            ))
        fig.add_hline(y=100, line_dash="dot", line_color=P["ok"], opacity=0.25,
                      annotation_text="100%", annotation_font_color=P["ok"], annotation_font_size=9)
        fig.update_layout(**_layout(
            title="TRENDING POR RAMA",
            yaxis=dict(range=[0,105], showgrid=True, gridcolor=P["border"], zeroline=False,
                       color=P["muted"], tickfont=dict(size=10), ticksuffix="%"),
            height=380, hovermode="x unified",
        ))
        return fig, df

    # Features
    def tab_feature_stats(self, days=30):
        features = self._cached("features", self.queries.get_feature_stats, ttl=120, days=days)
        if not features: return go.Figure(), go.Figure(), pd.DataFrame()
        df = pd.DataFrame(features)
        colors = [P["ok"] if r >= 90 else P["warn"] if r >= 70 else P["crit"] for r in df["pass_rate"]]
        fig1 = go.Figure(go.Bar(
            y=df["feature"], x=df["pass_rate"], orientation="h",
            marker=dict(color=colors, cornerradius=4),
            text=df["pass_rate"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside", textfont=dict(color=P["muted"], size=10),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
        ))
        fig1.update_layout(**_layout(
            title="PASS RATE POR MODULO",
            xaxis=dict(showgrid=True, gridcolor=P["border"], zeroline=False,
                       color=P["muted"], tickfont=dict(size=10), ticksuffix="%", range=[0,115]),
            height=320, bargap=0.45,
        ))
        tp, tf = df["passed"].sum(), df["failed"].sum()
        pct = round(tp/(tp+tf)*100 if (tp+tf) else 0)
        fig2 = go.Figure(go.Pie(
            labels=["TESTS PASARON","TESTS FALLARON"], values=[tp, tf], hole=0.68,
            marker=dict(colors=[P["ok"], P["crit"]], line=dict(color=P["bg"], width=3)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value}<br>%{percent}<extra></extra>",
        ))
        fig2.add_annotation(text=f"<b>{pct}%</b><br>exito", x=0.5, y=0.5, showarrow=False,
                            font=dict(color=P["text"], size=13, family="DM Mono,monospace"), align="center")
        fig2.update_layout(**_layout(title="RATIO GLOBAL", showlegend=True,
                                     height=320, margin=dict(t=44,b=16,l=8,r=8)))
        df_disp = df[["feature","total_tests","passed","failed","pass_rate"]].copy()
        df_disp.columns = ["MODULO","TOTAL TESTS","TESTS PASARON","TESTS FALLARON","PASS RATE %"]
        return fig1, fig2, df_disp

    # Flaky
    def tab_flaky_tests(self, days=30):
        flaky = self._cached("flaky", self.queries.get_flaky_tests, ttl=120, days=days, limit=20)
        if not flaky: return pd.DataFrame({"ESTADO": ["Sin flaky tests detectados"]})
        df = pd.DataFrame(flaky)
        df.columns = ["TEST ID","FLAKINESS %","FALLOS","TOTAL RUNS","ULTIMO RUN"]
        return df

    # Risk IA
    def tab_ai_risk(self, days=30):
        blockers = self._cached("blockers", self.queries.get_ai_blockers, ttl=120, days=days, limit=10)
        if not blockers:
            return "<div class='section-label'>RIESGO IA</div><p style='color:" + P["ok"] + ";font-size:15px'>OK Sin blockers criticos activos</p>"
        cards = []
        for b in blockers:
            pr   = b.get("pr_number","N/A")
            rama = b.get("branch","unknown")
            risk = b.get("overall_risk_level","LOW")
            text = b.get("ai_blockers","—")
            fecha = b.get("run_date","N/A")[:19].replace("T"," ")
            rc = {"CRITICAL":"crit","MEDIUM":"warn","LOW":"ok"}.get(risk,"ok")
            cc = {"CRITICAL":"critical","MEDIUM":"medium","LOW":"low"}.get(risk,"low")
            cards.append(f"""
<div class="risk-card {cc}">
  <div class="risk-meta">PR #{pr} &nbsp;·&nbsp; {rama} &nbsp;·&nbsp; {fecha}</div>
  <div style="margin-bottom:8px"><span class="badge {rc}">{risk}</span></div>
  <div class="risk-body">{text}</div>
</div>""")
        return "<div class='section-label'>ANALISIS DE RIESGOS IA</div>" + "".join(cards)

    # Timeline
    def tab_timeline(self, days=30):
        df = self._cached("timeline", self.queries.get_daily_pass_rate, ttl=120, days=days)
        if df.empty: return go.Figure(), df
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["pass_rate"], mode="lines+markers", name="Pass Rate",
            line=dict(color=P["accent"], width=2, shape="spline"),
            fill="tozeroy", fillcolor="rgba(129, 140, 248, 0.1)",
            marker=dict(size=7, color=[_risk_color(r) for r in df["risk_level"]],
                        line=dict(color=P["bg"], width=2)),
            hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
        ))
        for y, c, label in [(100, P["ok"],"100%"), (90, P["warn"],"90%")]:
            fig.add_hline(y=y, line_dash="dot", line_color=c, opacity=0.25,
                          annotation_text=label, annotation_font_color=c, annotation_font_size=9)
        fig.update_layout(**_layout(
            title="PASS RATE DIARIO",
            yaxis=dict(range=[0,105], showgrid=True, gridcolor=P["border"], zeroline=False,
                       color=P["muted"], tickfont=dict(size=10), ticksuffix="%"),
            height=380, hovermode="x unified",
        ))
        return fig, df



# -- Helpers --

def _layout(title="", height=400, **kw):
    base = dict(
        title=dict(text=f"<b>{title}</b>", font=dict(color=P["text"], size=14)),
        font=dict(family="DM Mono, monospace", color=P["muted"], size=11),
        paper_bgcolor=P["bg"], plot_bgcolor=P["bg"],
        xaxis=dict(color=P["muted"], showgrid=False, zeroline=False, tickfont=dict(color=P["muted"], size=10)),
        yaxis=dict(color=P["muted"], showgrid=False, zeroline=False, tickfont=dict(color=P["muted"], size=10)),
        margin=dict(t=48, b=32, l=44, r=16), height=height, hovermode="closest",
        showlegend=False,
    )
    base.update(kw)
    return base

def _risk_color(risk_str):
    return {"CRITICAL": P["crit"], "MEDIUM": P["warn"], "LOW": P["ok"]}.get(risk_str, P["ok"])

def create_gradio_app(queries: DashboardQueries) -> gr.Blocks:
    """Create Gradio app with custom CSS"""
    ui = DashboardUI(queries)
    
    with gr.Blocks(fill_height=True, title="Agent Karate Dashboard") as app:
        gr.Markdown(f"""
<div class="header">
  <div class="header-left">
    <div style="font-size: 28px; font-family: 'Syne', sans-serif; font-weight: 700; color: {P['text']};letter-spacing:-1px">agent karate</div>
    <div style="font-size: 13px; letter-spacing: 1px; color: {P['muted']}; margin-top: 2px; text-transform: uppercase;">quality metrics</div>
  </div>
  <div class="header-right" style="color: {P['muted']}; font-size: 13px">Powered by MongoDB + Karate + AI</div>
</div>""")
        
        global_days = gr.Radio([7, 14, 30, 60, 90], value=30, label="Rango de días (Global para todas las pestañas)")

        with gr.Tabs():
            # OVERVIEW TAB
            with gr.TabItem("Overview", id="overview"):
                overview_html = gr.HTML(value="Cargando...")
                
                def load_overview(d):
                    return ui.tab_overview(int(d))
                
                global_days.change(load_overview, inputs=global_days, outputs=overview_html)
                app.load(lambda: ui.tab_overview(30), outputs=overview_html)

            # TRENDING TAB
            with gr.TabItem("Trending", id="trending"):
                chart_tr = gr.Plot()
                table_tr = gr.Dataframe(interactive=False)
                
                def load_trending(d):
                    return ui.tab_branch_trending(int(d))
                
                global_days.change(load_trending, inputs=global_days, outputs=[chart_tr, table_tr])
                app.load(lambda: ui.tab_branch_trending(30), outputs=[chart_tr, table_tr])

            # MODULO TAB
            with gr.TabItem("Por Modulo", id="modulo"):
                chart1_mod = gr.Plot()
                chart2_mod = gr.Plot()
                table_mod = gr.Dataframe(interactive=False)
                
                def load_modulo(d):
                    return ui.tab_feature_stats(int(d))
                
                global_days.change(load_modulo, inputs=global_days, outputs=[chart1_mod, chart2_mod, table_mod])
                app.load(lambda: ui.tab_feature_stats(30), outputs=[chart1_mod, chart2_mod, table_mod])

            # FLAKY TAB
            with gr.TabItem("Flaky Tests", id="flaky"):
                table_fl = gr.Dataframe(interactive=False)
                
                def load_flaky(d):
                    return ui.tab_flaky_tests(int(d))
                
                global_days.change(load_flaky, inputs=global_days, outputs=table_fl)
                app.load(lambda: ui.tab_flaky_tests(30), outputs=table_fl)

            # RIESGO IA TAB
            with gr.TabItem("Riesgo IA", id="riesgo"):
                risk_html = gr.HTML(value="Cargando...")
                
                def load_risk(d):
                    return ui.tab_ai_risk(int(d))
                
                global_days.change(load_risk, inputs=global_days, outputs=risk_html)
                app.load(lambda: ui.tab_ai_risk(30), outputs=risk_html)

            # TIMELINE TAB
            with gr.TabItem("Timeline", id="timeline"):
                chart_tl = gr.Plot()
                table_tl = gr.Dataframe(interactive=False)
                
                def load_timeline(d):
                    return ui.tab_timeline(int(d))
                
                global_days.change(load_timeline, inputs=global_days, outputs=[chart_tl, table_tl])
                app.load(lambda: ui.tab_timeline(30), outputs=[chart_tl, table_tl])
    
    return app

def main():
    """Main entry point"""
    print("[Agent Karate Dashboard]")
    print("Initializing MongoDB connection...")
    
    try:
        sync = MongoSync()
        queries = DashboardQueries(sync)
        app = create_gradio_app(queries)
        
        port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
        print(f"Starting dashboard on http://localhost:{port}")
        print("Press Ctrl+C to stop")
        
        app.launch(
            server_name="0.0.0.0",
            server_port=port,
            show_error=True,
            quiet=False,
            css=CSS
        )
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        raise

if __name__ == "__main__":
    main()
