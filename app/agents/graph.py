# app/agents/graph.py
import os
import json
import time
from typing import TypedDict, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from app.agents.tools import evaluate_financial_health, search_regulatory_policies


class DueDiligenceState(TypedDict):
    company_name: str
    request_context: str
    financial_data: Dict[str, float]
    financial_report: str
    regulatory_report: str
    final_verdict: str
    next_step: str
    iteration_count: int
    execution_trace: List[Dict[str, Any]]


def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")
    )


def supervisor_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Agente Supervisor: decide qual especialista acionar ou se já pode consolidar."""
    start = time.time()
    iterations = state.get("iteration_count", 0) + 1
    has_financials = bool(state.get("financial_data"))
    fin_done = bool(state.get("financial_report"))
    reg_done = bool(state.get("regulatory_report"))

    # Roteamento determinístico aliado ao estado para garantir previsibilidade e zero loops
    if iterations > 5:
        decision = "compliance_reviewer"
        reason = "Limite de iterações atingido; encaminhando para consolidação."
    elif has_financials and not fin_done:
        decision = "financial_analyst"
        reason = "Dados financeiros detectados; acionando Analista Quantitativo."
    elif not reg_done:
        decision = "regulatory_researcher"
        reason = "Necessário verificar riscos normativos; acionando Pesquisador Regulatório."
    else:
        decision = "compliance_reviewer"
        reason = "Análises financeira e regulatória concluídas; encaminhando para Auditoria Final."

    trace = list(state.get("execution_trace", []))
    trace.append({
        "agent": "Supervisor (Router)",
        "action": f"Roteou para -> {decision}",
        "details": reason,
        "latency_ms": round((time.time() - start) * 1000, 2)
    })

    return {
        "next_step": decision,
        "iteration_count": iterations,
        "execution_trace": trace
    }


def financial_analyst_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Agente Analista Financeiro: executa ferramentas matemáticas e interpreta riscos."""
    start = time.time()
    metrics = evaluate_financial_health(state.get("financial_data", {}))
    llm = _get_llm()

    prompt = (
        f"Empresa analisada: {state['company_name']}\n"
        f"Contexto da operação: {state['request_context']}\n"
        f"Métricas calculadas via ferramenta: {json.dumps(metrics, ensure_ascii=False)}\n\n"
        "Redija um parecer técnico objetivo (máximo 2 parágrafos) avaliando a saúde financeira e os alertas."
    )

    response = llm.invoke([
        SystemMessage(content="Você é um Analista Financeiro Sênior especializado em Due Diligence e M&A."),
        HumanMessage(content=prompt)
    ])

    trace = list(state.get("execution_trace", []))
    trace.append({
        "agent": "Financial Analyst",
        "action": "Executou evaluate_financial_health() + Análise LLM",
        "details": f"Alertas identificados: {len(metrics['alertas_quantitativos'])}",
        "latency_ms": round((time.time() - start) * 1000, 2)
    })

    return {
        "financial_report": response.content,
        "execution_trace": trace
    }


def regulatory_researcher_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Agente Pesquisador Regulatório: consulta base normativa e avalia exposição legal."""
    start = time.time()
    query_text = f"{state['company_name']} {state['request_context']}"
    policies = search_regulatory_policies(query_text)
    llm = _get_llm()

    prompt = (
        f"Empresa analisada: {state['company_name']}\n"
        f"Contexto da operação: {state['request_context']}\n"
        f"Normativos aplicáveis recuperados: {json.dumps(policies, ensure_ascii=False)}\n\n"
        "Avalie os riscos regulatórios e jurídicos aplicáveis em até 2 parágrafos objetivos."
    )

    response = llm.invoke([
        SystemMessage(content="Você é um Especialista Regulatório e Jurídico Corporativo."),
        HumanMessage(content=prompt)
    ])

    trace = list(state.get("execution_trace", []))
    trace.append({
        "agent": "Regulatory Researcher",
        "action": "Executou search_regulatory_policies() + Análise LLM",
        "details": f"{len(policies)} normativos recuperados",
        "latency_ms": round((time.time() - start) * 1000, 2)
    })

    return {
        "regulatory_report": response.content,
        "execution_trace": trace
    }


def compliance_reviewer_node(state: DueDiligenceState) -> Dict[str, Any]:
    """Agente Revisor de Compliance: audita os relatórios anteriores e emite o veredito final."""
    start = time.time()
    llm = _get_llm()

    fin_section = state.get("financial_report") or "Nenhum dado financeiro foi submetido para cálculo."
    reg_section = state.get("regulatory_report") or "Nenhuma análise regulatória disponível."

    prompt = (
        f"Empresa: {state['company_name']}\n"
        f"Operação: {state['request_context']}\n\n"
        f"--- PARECER FINANCEIRO ---\n{fin_section}\n\n"
        f"--- PARECER REGULATÓRIO ---\n{reg_section}\n\n"
        "Consolide um Relatório Executivo de Due Diligence contendo:\n"
        "1. Classificação Geral de Risco (BAIXO, MÉDIO ou ALTO)\n"
        "2. Síntese dos Principais Riscos\n"
        "3. Recomendações de Mitigação antes da assinatura do contrato."
    )

    response = llm.invoke([
        SystemMessage(content="Você é o Diretor de Compliance e Risco. Seja rigoroso, imparcial e baseado exclusivamente nos pareceres fornecidos."),
        HumanMessage(content=prompt)
    ])

    trace = list(state.get("execution_trace", []))
    trace.append({
        "agent": "Compliance Reviewer",
        "action": "Consolidou pareceres e emitiu veredito final",
        "details": "Auditoria de consistência concluída",
        "latency_ms": round((time.time() - start) * 1000, 2)
    })

    return {
        "final_verdict": response.content,
        "execution_trace": trace
    }


def build_due_diligence_graph():
    workflow = StateGraph(DueDiligenceState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("financial_analyst", financial_analyst_node)
    workflow.add_node("regulatory_researcher", regulatory_researcher_node)
    workflow.add_node("compliance_reviewer", compliance_reviewer_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_step"],
        {
            "financial_analyst": "financial_analyst",
            "regulatory_researcher": "regulatory_researcher",
            "compliance_reviewer": "compliance_reviewer"
        }
    )

    workflow.add_edge("financial_analyst", "supervisor")
    workflow.add_edge("regulatory_researcher", "supervisor")
    workflow.add_edge("compliance_reviewer", END)

    return workflow.compile()


due_diligence_app = build_due_diligence_graph()