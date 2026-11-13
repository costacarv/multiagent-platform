from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.api.main import app
from app.agents.tools import evaluate_financial_health, search_regulatory_policies

client = TestClient(app)
HEADERS = {"X-API-Key": "mock_api_key_for_ci"}


def test_financial_health_tool_flags():
    """Valida cálculos determinísticos e geração de alertas de risco financeiro."""
    risky_data = {
        "receita_anual": 10000000.0,
        "ebitda": 800000.0,          # Margem 8% (< 10%)
        "divida_total": 4000000.0,   # Dívida/EBITDA = 5.0 (> 3.5)
        "patrimonio_liquido": 1500000.0,  # Dívida/PL = 2.67 (> 2.0)
        "ativo_circulante": 900000.0,
        "passivo_circulante": 1200000.0   # Liquidez = 0.75 (< 1.0)
    }
    result = evaluate_financial_health(risky_data)

    assert result["margem_ebitda_pct"] == 8.0
    assert result["liquidez_corrente"] == 0.75
    assert len(result["alertas_quantitativos"]) == 4


def test_regulatory_policies_tool():
    """Valida recuperação de normativos por palavras-chave."""
    policies = search_regulatory_policies("Empresa trata dados pessoais sob LGPD e participa de licitação")
    assert any("LGPD" in p for p in policies)
    assert any("Anticorrupção" in p for p in policies)


def test_analyze_unauthorized():
    """Bloqueia requisições sem X-API-Key válida."""
    response = client.post(
        "/analyze",
        json={"company_name": "Empresa Teste", "request_context": "Análise de risco societário."}
    )
    assert response.status_code == 401


@patch("app.agents.graph._get_llm")
def test_multiagent_full_flow_with_financials(mock_get_llm):
    """Testa o fluxo completo: Supervisor -> Financial -> Regulatory -> Compliance."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Parecer técnico simulado pelo mock.")
    mock_get_llm.return_value = mock_llm

    payload = {
        "company_name": "Alpha Tech S.A.",
        "request_context": "Aquisição societária envolvendo base de dados LGPD.",
        "financial_data": {
            "receita_anual": 5000000.0,
            "ebitda": 1000000.0,
            "divida_total": 1000000.0,
            "patrimonio_liquido": 2500000.0,
            "ativo_circulante": 1500000.0,
            "passivo_circulante": 1000000.0
        }
    }

    response = client.post("/analyze", json=payload, headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    agents_executed = [step["agent"] for step in data["execution_trace"]]

    assert "Financial Analyst" in agents_executed
    assert "Regulatory Researcher" in agents_executed
    assert "Compliance Reviewer" in agents_executed
    assert data["final_verdict"] == "Parecer técnico simulado pelo mock."


@patch("app.agents.graph._get_llm")
def test_multiagent_skips_financial_when_empty(mock_get_llm):
    """Testa o roteamento dinâmico pulando o Analista Financeiro quando não há balanço."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Parecer regulatório e compliance.")
    mock_get_llm.return_value = mock_llm

    payload = {
        "company_name": "Beta Serviços Ltda",
        "request_context": "Auditoria de contratos públicos e compliance anticorrupção."
    }

    response = client.post("/analyze", json=payload, headers=HEADERS)
    assert response.status_code == 200

    agents_executed = [step["agent"] for step in response.json()["execution_trace"]]
    assert "Financial Analyst" not in agents_executed
    assert "Regulatory Researcher" in agents_executed
    assert "Compliance Reviewer" in agents_executed