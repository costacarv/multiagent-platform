# app/agents/tools.py
from typing import Dict, Any, List

# app/agents/tools.py
import unicodedata
from typing import Dict, Any, List


def _normalize_text(text: str) -> str:
    """Remove acentos e converte para minúsculas para comparação consistente."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in nfkd if not unicodedata.combining(char))

def evaluate_financial_health(financials: Dict[str, float]) -> Dict[str, Any]:
    """Calcula indicadores de liquidez, alavancagem e margem operacional."""
    revenue = financials.get("receita_anual", 0.0)
    ebitda = financials.get("ebitda", 0.0)
    total_debt = financials.get("divida_total", 0.0)
    equity = financials.get("patrimonio_liquido", 1.0) or 1.0
    current_assets = financials.get("ativo_circulante", 0.0)
    current_liabilities = financials.get("passivo_circulante", 1.0) or 1.0

    ebitda_margin = round((ebitda / revenue) * 100, 2) if revenue > 0 else 0.0
    debt_to_equity = round(total_debt / equity, 2)
    current_liquidity = round(current_assets / current_liabilities, 2)
    net_debt_ebitda = round(total_debt / ebitda, 2) if ebitda > 0 else 99.0

    flags: List[str] = []
    if current_liquidity < 1.0:
        flags.append("Liquidez corrente abaixo de 1.0 (risco de caixa no curto prazo).")
    if debt_to_equity > 2.0:
        flags.append("Alavancagem elevada (Dívida/Patrimônio Líquido > 2.0).")
    if net_debt_ebitda > 3.5:
        flags.append("Relação Dívida/EBITDA crítica (> 3.5x).")
    if ebitda_margin < 10.0:
        flags.append("Margem EBITDA comprimida (< 10%).")

    return {
        "margem_ebitda_pct": ebitda_margin,
        "divida_sobre_pl": debt_to_equity,
        "liquidez_corrente": current_liquidity,
        "divida_sobre_ebitda": net_debt_ebitda,
        "alertas_quantitativos": flags if flags else ["Indicadores dentro dos parâmetros saudáveis."]
    }


def search_regulatory_policies(query: str) -> List[str]:
    """Simula busca vetorial (Qdrant) em normativos de Compliance, LGPD e CVM."""
    knowledge_base = [
        {
            "tags": ["dados", "lgpd", "vazamento", "privacidade", "clientes", "tecnologia"],
            "rule": "Lei 13.709/2018 (LGPD) Art. 46 e 52: Empresas que tratam dados pessoais sem criptografia ou registro de incidentes estão sujeitas a multas de até 2% do faturamento (limite de R$ 50 milhões por infração)."
        },
        {
            "tags": ["divida", "credito", "balanco", "auditoria", "cvm", "governanca", "fusao"],
            "rule": "Resolução CVM 80/2022 & Lei das S.A.: Passivos contingentes não divulgados em operações de M&A ou emissão de dívida acarretam responsabilidade solidária dos administradores."
        },
        {
            "tags": ["ambiental", "esg", "licenca", "ibama", "industria", "multa"],
            "rule": "Lei 9.605/1998 (Crimes Ambientais): Operações sem licenciamento ambiental válido implicam embargo imediato das atividades e bloqueio de linhas de crédito público."
        },
        {
            "tags": ["corrupcao", "licitacao", "governo", "compliance", "anticorrupcao", "contrato"],
            "rule": "Lei 12.846/2013 (Lei Anticorrupção): A ausência de programa de integridade efetivo agrava sanções administrativas em contratos com o setor público."
        }
    ]

    normalized_query = _normalize_text(query)
    matched = [
        item["rule"]
        for item in knowledge_base
        if any(_normalize_text(tag) in normalized_query for tag in item["tags"])
    ]

    if not matched:
        return [knowledge_base[0]["rule"], knowledge_base[1]["rule"]]
    return matched