# app/frontend/app.py
import os
import json
import logging
import requests
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Multi-Agent Due Diligence",
    page_icon="🏢",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")

st.title("🏢 Enterprise Multi-Agent Risk Platform — v2.0 (CI/CD)")
st.caption("Orquestração LangGraph • Supervisor + Analista Financeiro + Pesquisador Regulatório + Revisor de Compliance")

with st.form("due_diligence_form"):
    col1, col2 = st.columns([1, 1])

    with col1:
        company_name = st.text_input("Nome da Empresa Alvo", value="NovaTech Pagamentos S.A.")
        request_context = st.text_area(
            "Escopo da Análise / Contexto da Operação",
            value="Aquisição de 60% de participação societária. A empresa opera plataforma de crédito digital com grande base de dados de clientes e busca expandir contratos com órgãos públicos.",
            height=140
        )

    with col2:
        default_financials = {
            "receita_anual": 18000000.0,
            "ebitda": 1500000.0,
            "divida_total": 7200000.0,
            "patrimonio_liquido": 3000000.0,
            "ativo_circulante": 2100000.0,
            "passivo_circulante": 2500000.0
        }
        financial_input = st.text_area(
            "Indicadores Financeiros (JSON opcional)",
            value=json.dumps(default_financials, indent=2),
            height=195
        )

    submitted = st.form_submit_button("🚀 Iniciar Análise Multi-Agente", use_container_width=True)

if submitted:
    try:
        financial_data = json.loads(financial_input) if financial_input.strip() else {}
    except json.JSONDecodeError:
        st.error("⚠️ O campo de indicadores financeiros não contém um JSON válido.")
        st.stop()

    with st.spinner("Agentes colaborando na análise de risco..."):
        try:
            response = requests.post(
                f"{API_URL}/analyze",
                json={
                    "company_name": company_name,
                    "request_context": request_context,
                    "financial_data": financial_data
                },
                headers={"X-API-Key": API_KEY},
                timeout=45
            )

            if response.status_code == 200:
                data = response.json()

                st.subheader("📋 Parecer Executivo Consolidado (Compliance Reviewer)")
                st.markdown(data["final_verdict"])

                st.divider()
                col_fin, col_reg = st.columns(2)
                with col_fin:
                    st.subheader("📊 Parecer Financeiro")
                    st.info(data["financial_report"] or "Não aplicável.")
                with col_reg:
                    st.subheader("⚖️ Parecer Regulatório")
                    st.info(data["regulatory_report"] or "Não aplicável.")

                st.divider()
                st.subheader("🔍 Rastreabilidade da Orquestração (Execution Trace)")
                for idx, step in enumerate(data.get("execution_trace", []), 1):
                    st.markdown(
                        f"**Passo {idx} — `{step['agent']}`** ({step['latency_ms']} ms): "
                        f"{step['action']} — *{step['details']}*"
                    )
            else:
                logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                st.error("⚠️ Não foi possível concluir a análise no momento. Verifique os logs.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Falha de comunicação com a API: {e}")
            st.error("⚠️ Serviço temporariamente indisponível. Tente novamente em instantes.")