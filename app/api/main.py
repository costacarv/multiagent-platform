# app/api/main.py
import os
import time
import secrets
import logging
from typing import Dict, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import prometheus_client as prom
from prometheus_fastapi_instrumentator import Instrumentator

from app.agents.graph import due_diligence_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Multi-Agent Due Diligence API",
    version="1.0.0"
)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

WORKFLOW_RUNS = prom.Counter("multiagent_workflows_total", "Total de análises multi-agente executadas")
WORKFLOW_LATENCY = prom.Histogram(
    "multiagent_workflow_latency_seconds",
    "Latência total do grafo multi-agente",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0]
)


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="API_KEY não configurada no servidor.")
    if not api_key or not secrets.compare_digest(api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave de API inválida.")
    return api_key


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


class DueDiligenceRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=120)
    request_context: str = Field(..., min_length=10, max_length=1500)
    financial_data: Optional[Dict[str, float]] = None


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "multiagent-orchestrator"}


@app.post("/analyze", dependencies=[Depends(verify_api_key)])
def run_due_diligence(payload: DueDiligenceRequest):
    WORKFLOW_RUNS.inc()
    start_time = time.time()

    initial_state = {
        "company_name": payload.company_name.strip(),
        "request_context": payload.request_context.strip(),
        "financial_data": payload.financial_data or {},
        "financial_report": "",
        "regulatory_report": "",
        "final_verdict": "",
        "next_step": "",
        "iteration_count": 0,
        "execution_trace": []
    }

    try:
        result = due_diligence_app.invoke(initial_state)
        WORKFLOW_LATENCY.observe(time.time() - start_time)

        return {
            "company_name": result["company_name"],
            "final_verdict": result["final_verdict"],
            "financial_report": result["financial_report"],
            "regulatory_report": result["regulatory_report"],
            "execution_trace": result["execution_trace"]
        }
    except Exception as e:
        logger.error(f"Falha na execução do grafo multi-agente: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a análise multi-agente."
        )


Instrumentator().instrument(app).expose(app)