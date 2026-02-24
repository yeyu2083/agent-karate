#!/usr/bin/env python3
"""
📊 Dashboard de Riesgo y Calidad - Agent Karate

Interfaz interactiva Gradio para visualizar métricas de testing:
- KPIs principales (pass rate, risk level, total tests)
- Trending por rama (últimos 30 días)
- Desglose por feature (Users vs Posts vs Auth)
- Tests flaky (inestables)
- Riesgo y blockers IA
- Timeline de ejecuciones

Usage:
    python agent/dashboard.py
    Abre http://localhost:7860
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Tuple
import json

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Agregar el directorio padre al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import gradio as gr
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    from pymongo import MongoClient
except ImportError as e:
    raise ImportError(
        f"Missing dependencies: {e}\n"
        f"Install: pip install gradio plotly pandas pymongo"
    )

# Importar MongoSync - intentar relativo primero, luego absoluto
try:
    from .mongo_sync import MongoSync
except ImportError:
    # Cuando se ejecuta directamente: python agent/dashboard.py
    try:
        from agent.mongo_sync import MongoSync
    except ImportError as e:
        print(f"❌ Error importando mongo_sync: {e}")
        sys.exit(1)


class DashboardQueries:
    """🔍 Funciones de queries a MongoDB para dashboard"""

    def __init__(self, mongo_sync: MongoSync):
        """
        Args:
            mongo_sync: Instancia de MongoSync conectada
        """
        self.mongo = mongo_sync
        if not mongo_sync.enabled:
            raise RuntimeError("MongoDB no está disponible. Verifica la conexión.")
        self.db = mongo_sync.db

    def get_latest_executions(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """
        📋 Obtener las últimas N ejecuciones en los últimos D días
        
        Returns:
            List[dict]: [{execution_batch_id, run_date, branch, overall_pass_rate, 
                        overall_risk_level, failed_tests, total_tests}, ...]
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["execution_summaries"]
            
            results = list(
                collection.find(
                    {"run_date": {"$gte": start_date}}
                )
                .sort("run_date", -1)
                .limit(limit)
            )
            
            # Limpiar ObjectId para JSON serialization
            for doc in results:
                doc["_id"] = str(doc["_id"])
                doc["run_date"] = doc["run_date"].isoformat()
            
            return results
        except Exception as e:
            print(f"❌ Error en get_latest_executions: {e}")
            return []

    def get_kpis_summary(self, days: int = 30) -> Dict:
        """
        📊 Obtener KPIs agregados de los últimos D días
        
        Returns:
            {total_tests, passed_tests, failed_tests, overall_pass_rate%, risk_level}
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["execution_summaries"]
            
            pipeline = [
                {
                    "$match": {"run_date": {"$gte": start_date}}
                },
                {
                    "$group": {
                        "_id": None,
                        "total_tests": {"$sum": "$total_tests"},
                        "passed_tests": {"$sum": "$passed_tests"},
                        "failed_tests": {"$sum": "$failed_tests"},
                        "avg_pass_rate": {"$avg": "$overall_pass_rate"},
                        "critical_count": {
                            "$sum": {"$cond": [
                                {"$eq": ["$overall_risk_level", "CRITICAL"]}, 1, 0
                            ]}
                        },
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            if results:
                data = results[0]
                overall_pass_rate = data["avg_pass_rate"]
                
                if overall_pass_rate == 100:
                    risk = "LOW"
                elif overall_pass_rate >= 90:
                    risk = "MEDIUM"
                else:
                    risk = "CRITICAL"
                
                return {
                    "total_tests": int(data["total_tests"]),
                    "passed_tests": int(data["passed_tests"]),
                    "failed_tests": int(data["failed_tests"]),
                    "overall_pass_rate": round(overall_pass_rate, 2),
                    "overall_risk_level": risk,
                    "critical_runs": int(data["critical_count"]),
                }
            
            return {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "overall_pass_rate": 0,
                "overall_risk_level": "UNKNOWN",
                "critical_runs": 0,
            }
        except Exception as e:
            print(f"❌ Error en get_kpis_summary: {e}")
            return {}

    def get_branch_trending(self, days: int = 30, limit_branches: int = 5) -> pd.DataFrame:
        """
        📈 Obtener trending de pass_rate por rama
        
        Args:
            days: Días a analizar
            limit_branches: Top N ramas a mostrar
        
        Returns:
            DataFrame: {date, branch, pass_rate}
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["execution_summaries"]
            
            # Pipeline para obtener top branches
            pipeline_top_branches = [
                {"$match": {"run_date": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": "$branch",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": limit_branches},
            ]
            
            top_branches = list(collection.aggregate(pipeline_top_branches))
            branch_names = [b["_id"] for b in top_branches]
            
            if not branch_names:
                return pd.DataFrame()
            
            # Pipeline para obtener datos diarios por rama
            pipeline_daily = [
                {
                    "$match": {
                        "run_date": {"$gte": start_date},
                        "branch": {"$in": branch_names}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "branch": "$branch",
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$run_date"}}
                        },
                        "avg_pass_rate": {"$avg": "$overall_pass_rate"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.date": 1}},
            ]
            
            results = list(collection.aggregate(pipeline_daily))
            
            # Convertir a DataFrame
            data = []
            for doc in results:
                data.append({
                    "date": doc["_id"]["date"],
                    "branch": doc["_id"]["branch"],
                    "pass_rate": round(doc["avg_pass_rate"], 2),
                })
            
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            print(f"❌ Error en get_branch_trending: {e}")
            return pd.DataFrame()

    def get_feature_stats(self, days: int = 30) -> List[Dict]:
        """
        📊 Estadísticas por feature (Users, Posts, Auth)
        
        Returns:
            [{feature, total_tests, passed, failed, pass_rate, avg_duration_ms}, ...]
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["test_results"]
            
            pipeline = [
                {"$match": {"run_date": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": "$feature",
                        "total": {"$sum": 1},
                        "passed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "passed"]}, 1, 0]}
                        },
                        "failed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "avg_duration_ms": {"$avg": "$duration_ms"},
                    }
                },
                {"$sort": {"total": -1}},
            ]
            
            results = list(collection.aggregate(pipeline))
            
            data = []
            for doc in results:
                pass_rate = (doc["passed"] / doc["total"] * 100) if doc["total"] > 0 else 0
                data.append({
                    "feature": doc["_id"],
                    "total_tests": int(doc["total"]),
                    "passed": int(doc["passed"]),
                    "failed": int(doc["failed"]),
                    "pass_rate": round(pass_rate, 2),
                    "avg_duration_ms": round(doc["avg_duration_ms"], 2),
                })
            
            return data
        except Exception as e:
            print(f"❌ Error en get_feature_stats: {e}")
            return []

    def get_flaky_tests(self, days: int = 30, min_flakiness: float = 0.3, limit: int = 20) -> List[Dict]:
        """
        🔴 Tests inestables (flaky) - fallan ocasionalmente
        
        Args:
            days: Días a analizar
            min_flakiness: Umbral mínimo de inestabilidad (0.3 = 30%)
            limit: Top N flaky tests a mostrar
        
        Returns:
            [{test_id, flakiness%, failure_count, total_runs, last_run_date}, ...]
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["test_results"]
            
            pipeline = [
                {"$match": {"run_date": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": "$test_id",
                        "total": {"$sum": 1},
                        "failed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "last_run_date": {"$max": "$run_date"},
                    }
                },
                {
                    "$project": {
                        "test_id": "$_id",
                        "flakiness": {"$divide": ["$failed", "$total"]},
                        "failure_count": "$failed",
                        "total_runs": "$total",
                        "last_run_date": 1,
                    }
                },
                {"$match": {"flakiness": {"$gte": min_flakiness}}},
                {"$sort": {"flakiness": -1}},
                {"$limit": limit},
            ]
            
            results = list(collection.aggregate(pipeline))
            
            data = []
            for doc in results:
                data.append({
                    "test_id": doc["test_id"],
                    "flakiness_pct": round(doc["flakiness"] * 100, 1),
                    "failure_count": int(doc["failure_count"]),
                    "total_runs": int(doc["total_runs"]),
                    "last_run_date": doc["last_run_date"].isoformat() if doc["last_run_date"] else "N/A",
                })
            
            return data
        except Exception as e:
            print(f"❌ Error en get_flaky_tests: {e}")
            return []

    def get_ai_blockers(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        🤖 Riesgos críticos y blockers identificados por IA
        
        Returns:
            [{pr_number, branch, overall_risk_level, ai_blockers, run_date}, ...]
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["execution_summaries"]
            
            results = list(
                collection.find({
                    "run_date": {"$gte": start_date},
                    "ai_blockers": {"$exists": True, "$ne": []}
                })
                .sort("run_date", -1)
                .limit(limit)
            )
            
            data = []
            for doc in results:
                data.append({
                    "pr_number": doc.get("pr_number", "N/A"),
                    "branch": doc.get("branch", "unknown"),
                    "overall_risk_level": doc.get("overall_risk_level"),
                    "ai_blockers": ", ".join(doc.get("ai_blockers", [])) or "None",
                    "run_date": doc["run_date"].isoformat(),
                })
            
            return data
        except Exception as e:
            print(f"❌ Error en get_ai_blockers: {e}")
            return []

    def get_daily_pass_rate(self, days: int = 30) -> pd.DataFrame:
        """
        📈 Pass rate diario (última ejecución por día)
        
        Returns:
            DataFrame: {date, pass_rate, risk_level}
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            collection = self.db["execution_summaries"]
            
            pipeline = [
                {"$match": {"run_date": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$run_date"}},
                        "avg_pass_rate": {"$avg": "$overall_pass_rate"},
                        "most_common_risk": {"$first": "$overall_risk_level"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
            
            results = list(collection.aggregate(pipeline))
            
            data = []
            for doc in results:
                data.append({
                    "date": doc["_id"],
                    "pass_rate": round(doc["avg_pass_rate"], 2),
                    "risk_level": doc["most_common_risk"],
                })
            
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            print(f"❌ Error en get_daily_pass_rate: {e}")
            return pd.DataFrame()


class DashboardUI:
    """🎨 Interfaz Gradio del Dashboard"""

    def __init__(self, queries: DashboardQueries):
        """
        Args:
            queries: Instancia de DashboardQueries
        """
        self.queries = queries
        self.cache_time = {}
        self.cache_data = {}

    def _get_cached_data(self, key: str, fetch_fn, ttl_seconds: int = 30, *args, **kwargs):
        """
        Cache simple para evitar sobrecargar MongoDB
        
        Args:
            key: Clave de cache
            fetch_fn: Función para obtener datos
            ttl_seconds: Tiempo de vida del cache
        """
        now = datetime.now(timezone.utc)
        
        if key in self.cache_time:
            if (now - self.cache_time[key]).total_seconds() < ttl_seconds:
                return self.cache_data[key]
        
        data = fetch_fn(*args, **kwargs)
        self.cache_time[key] = now
        self.cache_data[key] = data
        return data

    def refresh_cache(self):
        """Limpia el cache para obtener datos frescos"""
        self.cache_time.clear()
        self.cache_data.clear()

    # ==================== TAB 1: OVERVIEW ====================
    
    def tab_overview(self, days_selector: int = 30) -> Tuple:
        """
        📊 Tab 1: KPIs principales + tabla de últimas ejecuciones
        """
        # KPIs
        kpis = self._get_cached_data(
            "kpis",
            self.queries.get_kpis_summary,
            ttl_seconds=60,
            days=days_selector
        )
        
        # Últimas ejecuciones
        executions = self._get_cached_data(
            "latest_executions",
            self.queries.get_latest_executions,
            ttl_seconds=60,
            limit=10,
            days=days_selector
        )
        
        # Crear tabla
        exec_df = pd.DataFrame(executions)[
            ["execution_batch_id", "run_date", "branch", "overall_pass_rate", 
             "overall_risk_level", "passed_tests", "failed_tests"]
        ] if executions else pd.DataFrame()
        
        # Renombrar columnas
        if not exec_df.empty:
            exec_df.columns = ["Batch ID", "Fecha", "Rama", "Pass Rate %", "Riesgo", "Pasados", "Fallidos"]
        
        # KPI text con colores y emojis
        pass_rate = kpis.get('overall_pass_rate', 0)
        risk_level = kpis.get('overall_risk_level', 'UNKNOWN')
        
        # Color según riesgo
        if risk_level == "LOW":
            risk_emoji = "🟢"
        elif risk_level == "MEDIUM":
            risk_emoji = "🟡"
        else:
            risk_emoji = "🔴"
        
        # Color según pass rate
        if pass_rate == 100:
            status_emoji = "✅"
        elif pass_rate >= 90:
            status_emoji = "⚠️"
        else:
            status_emoji = "❌"
        
        kpi_text = f"""
### {status_emoji} KPIs Generales ({ days_selector} últimos días)

| Métrica | Valor |
|---------|-------|
| **Total Tests Ejecutados** | **{kpis.get('total_tests', 0)}** 🧪 |
| **✅ Pasaron** | **{kpis.get('passed_tests', 0)}** (Verde = Bien!) |
| **❌ Fallaron** | **{kpis.get('failed_tests', 0)}** (Rojo = Revisar) |
| **📈 Porcentaje Éxito** | **{kpis.get('overall_pass_rate', 0)}%** |
| **{risk_emoji} Estado General** | **{risk_level}** |
| **🚨 Ejecuciones Críticas** | **{kpis.get('critical_runs', 0)}** |

---

#### 🎯 Lo que significa:
- **🟢 LOW**: Todo bien, sin preocupaciones
- **🟡 MEDIUM**: Revisar, hay algunos fallos
- **🔴 CRITICAL**: Atención urgente, muchos fallos

#### 📊 Histórico reciente (últimas ejecuciones):
"""
        
        return kpi_text, exec_df

    # ==================== TAB 2: TRENDING POR RAMA ====================
    
    def tab_branch_trending(self, days_selector: int = 30) -> Tuple:
        """
        📈 Tab 2: Gráfico de trending por rama + tabla
        """
        df = self._get_cached_data(
            "branch_trending",
            self.queries.get_branch_trending,
            ttl_seconds=120,
            days=days_selector
        )
        
        if df.empty:
            return "Sin datos de trending por rama", None
        
        # Gráfico mejorado con colores
        fig = px.line(
            df,
            x="date",
            y="pass_rate",
            color="branch",
            title=f"📈 Tendencia de Calidad por Rama ({days_selector} días)<br><sub>¿Está mejorando o empeorando?</sub>",
            labels={"date": "Fecha", "pass_rate": "% Éxito", "branch": "Rama"},
            markers=True,
            height=500,
        )
        
        # Mejorar apariencia
        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{fullData.name}</b><br>Fecha: %{x}<br>Éxito: %{y:.1f}%<extra></extra>"
        )
        
        fig.update_layout(
            hovermode="x unified",
            yaxis_range=[0, 105],
            template="plotly_dark",
            font=dict(size=12),
            xaxis_title="📅 Fecha",
            yaxis_title="📊 Porcentaje de Éxito (%)",
        )
        
        # Agregar línea de referencia al 100%
        fig.add_hline(y=100, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Meta: 100%")
        
        return fig, df

    # ==================== TAB 3: POR FEATURE ====================
    
    def tab_feature_stats(self, days_selector: int = 30) -> Tuple:
        """
        📊 Tab 3: Estadísticas por feature (Users, Posts, Auth)
        """
        features = self._get_cached_data(
            "feature_stats",
            self.queries.get_feature_stats,
            ttl_seconds=120,
            days=days_selector
        )
        
        if not features:
            return None, "Sin datos de features"
        
        df = pd.DataFrame(features)
        
        # Gráfico 1: Barras horizontales (más intuitivo)
        fig1 = go.Figure()
        
        # Agregar barras con colores
        colors = ["#2ecc71" if row["pass_rate"] >= 90 else "#f39c12" if row["pass_rate"] >= 70 else "#e74c3c" 
                  for _, row in df.iterrows()]
        
        fig1.add_trace(go.Bar(
            y=df["feature"],
            x=df["pass_rate"],
            marker=dict(color=colors),
            name="Éxito %",
            text=df["pass_rate"].apply(lambda x: f"{x:.0f}%"),
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Éxito: %{x:.1f}%<extra></extra>"
        ))
        
        fig1.update_layout(
            title="🎯 Calidad por Módulo<br><sub>Verde = Excelente | Naranja = Bueno | Rojo = Revisar</sub>",
            xaxis_title="📊 % de Éxito",
            yaxis_title="🔧 Módulo",
            height=400,
            template="plotly_dark",
            font=dict(size=12),
        )
        
        # Gráfico 2: Pie chart de éxito vs fracaso global
        total_passed = df["passed"].sum()
        total_failed = df["failed"].sum()
        
        fig2 = go.Figure(data=[go.Pie(
            labels=["✅ PASARON", "❌ FALLARON"],
            values=[total_passed, total_failed],
            marker=dict(colors=["#2ecc71", "#e74c3c"]),
            hole=0.3,
            text=[f"✅ {total_passed}", f"❌ {total_failed}"],
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>Tests: %{value}<extra></extra>"
        )])
        
        fig2.update_layout(
            title="📈 Ratio de Éxito Global<br><sub>Visión rápida de la salud</sub>",
            height=400,
            template="plotly_dark",
            font=dict(size=12),
        )
        
        # Tabla resumen
        df_display = df[["feature", "total_tests", "passed", "failed", "pass_rate"]].copy()
        df_display.columns = ["Módulo", "Total", "✅ Pasaron", "❌ Fallaron", "Éxito %"]
        
        return fig1, fig2, df_display

    # ==================== TAB 4: FLAKY TESTS ====================
    
    def tab_flaky_tests(self, days_selector: int = 30) -> pd.DataFrame:
        """
        🔴 Tab 4: Tests inestables
        """
        flaky = self._get_cached_data(
            "flaky_tests",
            self.queries.get_flaky_tests,
            ttl_seconds=120,
            days=days_selector,
            limit=20
        )
        
        if not flaky:
            return pd.DataFrame({"Mensaje": ["Sin tests flaky detectados"]})
        
        df = pd.DataFrame(flaky)
        df.columns = ["Test ID", "Flakiness %", "Fallos", "Total Runs", "Última Ejecución"]
        
        return df

    # ==================== TAB 5: RIESGO IA ====================
    
    def tab_ai_risk(self, days_selector: int = 30) -> pd.DataFrame:
        """
        🤖 Tab 5: Blockers y riesgos IA
        """
        blockers = self._get_cached_data(
            "ai_blockers",
            self.queries.get_ai_blockers,
            ttl_seconds=120,
            days=days_selector,
            limit=10
        )
        
        if not blockers:
            return pd.DataFrame({"Mensaje": ["Sin blockers críticos detectados"]})
        
        df = pd.DataFrame(blockers)
        df.columns = ["PR", "Rama", "Risk Level", "AI Blockers", "Fecha"]
        
        return df

    # ==================== TAB 6: TIMELINE ====================
    
    def tab_timeline(self, days_selector: int = 30) -> Tuple:
        """
        📈 Tab 6: Timeline de pass_rate diario con área coloreada por riesgo
        """
        df = self._get_cached_data(
            "daily_pass_rate",
            self.queries.get_daily_pass_rate,
            ttl_seconds=120,
            days=days_selector
        )
        
        if df.empty:
            return None, "Sin datos de timeline"
        
        # Asignar colores según risk level
        df["color"] = df["risk_level"].map({
            "LOW": "green",
            "MEDIUM": "orange",
            "CRITICAL": "red",
        })
        
        # Gráfico con área coloreada
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["pass_rate"],
            fill="tozeroy",
            mode="lines+markers",
            name="Pass Rate %",
            line=dict(color="blue"),
            fillcolor="rgba(0, 100, 200, 0.2)",
            marker=dict(size=8),
        ))
        
        fig.update_layout(
            title=f"Pass Rate Timeline ({days_selector} días)",
            xaxis_title="Fecha",
            yaxis_title="Pass Rate %",
            height=400,
            hovermode="x unified",
            yaxis_range=[0, 105],
        )
        
        return fig, df


def create_gradio_app(mongo_sync: MongoSync) -> gr.Blocks:
    """
    🎨 Crea la aplicación Gradio con todos los tabs
    """
    queries = DashboardQueries(mongo_sync)
    ui = DashboardUI(queries)
    
    with gr.Blocks(title="Dashboard Karate - Riesgo & Calidad") as app:
        gr.Markdown("# 📊 Dashboard de Riesgo y Calidad - Agent Karate")
        gr.Markdown("Visualización en tiempo real de métricas de testing, tendencias y análisis IA")
        
        # Controles globales
        with gr.Row():
            days_selector = gr.Radio(
                label="📅 Período",
                choices=[7, 14, 30],
                value=30,
                scale=1,
            )
            refresh_btn = gr.Button("🔄 Refresh", scale=1)
            
            def on_refresh():
                ui.refresh_cache()
                return "✅ Cache limpiado. Datos actualizados."
            
            refresh_status = gr.Textbox(label="Estado", interactive=False, value="Listo")
            refresh_btn.click(on_refresh, outputs=refresh_status)
        
        # ==================== TABS ====================
        
        with gr.Tabs():
            # ==================== TAB 1: OVERVIEW ====================
            with gr.Tab("📊 Overview"):
                kpi_md = gr.Markdown()
                exec_table = gr.Dataframe(headers=["Batch ID", "Fecha", "Rama", "Pass Rate %", "Riesgo", "Pasados", "Fallidos"])
                
                def update_overview(days):
                    return ui.tab_overview(days)
                
                days_selector.change(update_overview, inputs=days_selector, outputs=[kpi_md, exec_table])
                app.load(update_overview, inputs=days_selector, outputs=[kpi_md, exec_table])
            
            # ==================== TAB 2: TRENDING ====================
            with gr.Tab("📈 Trending por Rama"):
                trend_plot = gr.Plot()
                trend_table = gr.Dataframe()
                
                def update_trending(days):
                    fig, df = ui.tab_branch_trending(days)
                    return fig, df
                
                days_selector.change(update_trending, inputs=days_selector, outputs=[trend_plot, trend_table])
                app.load(update_trending, inputs=days_selector, outputs=[trend_plot, trend_table])
            
            # ==================== TAB 3: FEATURES ====================
            with gr.Tab("🎯 Por Módulo"):
                with gr.Row():
                    feat_plot1 = gr.Plot()
                    feat_plot2 = gr.Plot()
                feat_table = gr.Dataframe()
                
                def update_features(days):
                    fig1, fig2, df = ui.tab_feature_stats(days)
                    return fig1, fig2, df
                
                days_selector.change(update_features, inputs=days_selector, outputs=[feat_plot1, feat_plot2, feat_table])
                app.load(update_features, inputs=days_selector, outputs=[feat_plot1, feat_plot2, feat_table])
            
            # ==================== TAB 4: FLAKY ====================
            with gr.Tab("🔴 Flaky Tests"):
                flaky_table = gr.Dataframe()
                
                def update_flaky(days):
                    return ui.tab_flaky_tests(days)
                
                days_selector.change(update_flaky, inputs=days_selector, outputs=flaky_table)
                app.load(update_flaky, inputs=days_selector, outputs=flaky_table)
            
            # ==================== TAB 5: RISK IA ====================
            with gr.Tab("🤖 Riesgo IA"):
                risk_table = gr.Dataframe()
                
                def update_risk(days):
                    return ui.tab_ai_risk(days)
                
                days_selector.change(update_risk, inputs=days_selector, outputs=risk_table)
                app.load(update_risk, inputs=days_selector, outputs=risk_table)
            
            # ==================== TAB 6: TIMELINE ====================
            with gr.Tab("⏰ Timeline"):
                timeline_plot = gr.Plot()
                timeline_table = gr.Dataframe()
                
                def update_timeline(days):
                    fig, df = ui.tab_timeline(days)
                    return fig, df
                
                days_selector.change(update_timeline, inputs=days_selector, outputs=[timeline_plot, timeline_table])
                app.load(update_timeline, inputs=days_selector, outputs=[timeline_plot, timeline_table])
    
    return app


def main():
    """Punto de entrada principal"""
    print("🚀 Iniciando Dashboard de Riesgo y Calidad...")
    
    # Conectar a MongoDB
    mongo_sync = MongoSync()
    if not mongo_sync.enabled:
        print("❌ No se pudo conectar a MongoDB. Verifica la configuración.")
        return
    
    # Crear app Gradio
    app = create_gradio_app(mongo_sync)
    
    # Iniciar servidor
    print("📊 Dashboard disponible en: http://localhost:7860")
    print("   Presiona Ctrl+C para detener")
    
    try:
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            theme=gr.themes.Soft(),
        )
    except KeyboardInterrupt:
        print("\n✓ Dashboard detenido")
    finally:
        mongo_sync.close()


if __name__ == "__main__":
    main()
