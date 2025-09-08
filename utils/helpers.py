"""
Utilitários auxiliares - Agente PowerBI
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def format_number(num: int) -> str:
    """Formata números com separadores"""
    return f"{num:,}".replace(',', '.')

def clean_text(text: str) -> str:
    """Limpa texto removendo caracteres especiais"""
    if not isinstance(text, str):
        return str(text)
    
    # Remove quebras de linha extras e espaços
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def safe_get(data: Dict, key: str, default: Any = "N/A") -> Any:
    """Obtém valor de dicionário com fallback seguro"""
    return data.get(key, default) if isinstance(data, dict) else default

def parse_date(date_str: str) -> Optional[datetime]:
    """Tenta fazer parse de string de data em vários formatos"""
    if not isinstance(date_str, str):
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", 
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def get_period_filter(period: str) -> Dict[str, datetime]:
    """Retorna filtros de data baseado no período"""
    
    now = datetime.now()
    
    filters = {
        "hoje": {
            "start": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "end": now
        },
        "ontem": {
            "start": (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            "end": (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        },
        "esta_semana": {
            "start": now - timedelta(days=now.weekday()),
            "end": now
        },
        "este_mes": {
            "start": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "end": now
        },
        "ultimos_7_dias": {
            "start": now - timedelta(days=7),
            "end": now
        },
        "ultimos_30_dias": {
            "start": now - timedelta(days=30),
            "end": now
        }
    }
    
    return filters.get(period.lower().replace(' ', '_'), {
        "start": now - timedelta(days=30),
        "end": now
    })

def calculate_conversion_rate(leads: List[Dict], status_field: str = "situacao") -> Dict[str, float]:
    """Calcula taxas de conversão"""
    
    if not leads:
        return {}
    
    total = len(leads)
    conversions = {}
    
    for lead in leads:
        status = lead.get(status_field, "").upper()
        
        if "VENDA" in status or "VENDIDO" in status:
            conversions["vendas"] = conversions.get("vendas", 0) + 1
        elif "RESERVA" in status:
            conversions["reservas"] = conversions.get("reservas", 0) + 1
        elif "ATENDIMENTO" in status:
            conversions["em_atendimento"] = conversions.get("em_atendimento", 0) + 1
    
    # Calcula percentuais
    rates = {}
    for key, count in conversions.items():
        rates[key] = round((count / total) * 100, 2)
    
    return rates

def extract_insights(leads: List[Dict]) -> List[str]:
    """Extrai insights automáticos dos dados"""
    
    if not leads:
        return ["Nenhum dado disponível para análise"]
    
    insights = []
    total = len(leads)
    
    # Análise básica
    insights.append(f"Total de {total} leads analisados")
    
    # Top situações
    situacoes = {}
    for lead in leads:
        sit = lead.get('situacao', 'N/A')
        situacoes[sit] = situacoes.get(sit, 0) + 1
    
    if situacoes:
        top_situacao = max(situacoes.items(), key=lambda x: x[1])
        pct = round((top_situacao[1] / total) * 100, 1)
        insights.append(f"Situação predominante: {top_situacao[0]} ({pct}%)")
    
    # Top origens
    origens = {}
    for lead in leads:
        origem = lead.get('origem_nome', lead.get('origem', 'N/A'))
        origens[origem] = origens.get(origem, 0) + 1
    
    if origens:
        top_origem = max(origens.items(), key=lambda x: x[1])
        pct = round((top_origem[1] / total) * 100, 1)
        insights.append(f"Principal origem: {top_origem[0]} ({pct}%)")
    
    # Análise temporal (se disponível)
    dates = []
    for lead in leads:
        date_str = lead.get('data_cad')
        if date_str:
            parsed = parse_date(date_str)
            if parsed:
                dates.append(parsed)
    
    if dates:
        dates.sort()
        periodo_dias = (dates[-1] - dates[0]).days
        if periodo_dias > 0:
            insights.append(f"Período analisado: {periodo_dias} dias")
        
        # Média por dia
        media_dia = len(dates) / max(periodo_dias, 1)
        insights.append(f"Média: {media_dia:.1f} leads/dia")
    
    return insights

def validate_leads_data(leads: List[Dict]) -> Dict[str, Any]:
    """Valida qualidade dos dados de leads"""
    
    if not leads:
        return {"valid": False, "error": "Lista de leads vazia"}
    
    validation = {
        "valid": True,
        "total_records": len(leads),
        "fields_analysis": {},
        "data_quality": {}
    }
    
    # Analisa campos comuns
    common_fields = ['nome', 'situacao', 'origem_nome', 'data_cad', 'email']
    
    for field in common_fields:
        field_data = [lead.get(field) for lead in leads]
        non_empty = [d for d in field_data if d and str(d).strip()]
        
        validation["fields_analysis"][field] = {
            "present": len(non_empty),
            "missing": len(leads) - len(non_empty),
            "coverage": round((len(non_empty) / len(leads)) * 100, 1)
        }
    
    # Qualidade geral
    avg_coverage = sum(f["coverage"] for f in validation["fields_analysis"].values()) / len(common_fields)
    validation["data_quality"]["average_field_coverage"] = round(avg_coverage, 1)
    validation["data_quality"]["quality_score"] = "Excelente" if avg_coverage >= 90 else "Boa" if avg_coverage >= 70 else "Regular"
    
    return validation