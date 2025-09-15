"""
Analisador Corrigido - CVDW
Corrige as discrepâncias identificadas comparando com Power BI
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import re

class CorrectedCVDWAnalyzer:
    """Analisador corrigido para bater com dados do Power BI"""
    
    def __init__(self):
        # Mapeamento de responsáveis padronizado (baseado no Power BI)
        self.responsavel_mapping = {
            # Padrão: nome_completo -> nome_padronizado
            "lucia": "Lucia AL",
            "luana": "Luana AL", 
            "vagner": "Vagner F",
            "beatriz": "Beatriz R",
            "bruno": "Bruno R",
            "vagner ferreira": "Vagner F",
            "lucia alexandra": "Lucia AL",
            "luana alexandra": "Luana AL"
        }
        
        # Mapeamento de origens padronizado (BASEADO NOS DADOS REAIS)
        self.origem_mapping = {
            "chatbot": "WhatsApp",  # ChatBot na API = WhatsApp no Power BI
            "facebook": "Facebook",
            "instagram": "Instagram", 
            "meta": "Meta Org",
            "whatsapp": "WhatsApp",
            "ugello": "Ugello",
            "portal": "Portal",
            "painel gestor": "Gestor",  # Painel Gestor encontrado na API
            "gestor": "Gestor",
            "meta org": "Meta Org",
            "meta ads": "Facebook",
            "insta": "Instagram",
            "botmaker": "WhatsApp"  # BOTMAKER encontrado na API
        }
    
    def normalize_responsavel_name(self, name: str) -> str:
        """Normaliza nome do responsável conforme Power BI"""
        
        if not name or pd.isna(name):
            return "Não Informado"
        
        name_lower = str(name).lower().strip()
        
        # Busca por matches parciais
        for key, standard_name in self.responsavel_mapping.items():
            if key in name_lower:
                return standard_name
        
        # Se não encontrou, retorna nome resumido
        parts = name_lower.split()
        if len(parts) >= 2:
            return f"{parts[0].title()} {parts[1][0].upper()}"
        else:
            return name.title()[:15]  # Limita tamanho
    
    def normalize_origem_name(self, origem: str) -> str:
        """Normaliza nome da origem conforme Power BI"""
        
        if not origem or pd.isna(origem):
            return "Não Informado"
        
        origem_lower = str(origem).lower().strip()
        
        # Busca por matches exatos ou parciais
        for key, standard_name in self.origem_mapping.items():
            if key in origem_lower or origem_lower in key:
                return standard_name
        
        # Retorna original capitalizado se não encontrou
        return str(origem).title()
    
    def filter_leads_by_period(self, leads: List[Dict], period_days: int = 30, focus_previous_month: bool = True) -> List[Dict]:
        """Filtra leads por período, priorizando mês anterior fechado"""

        if not leads:
            return []

        # Define período baseado no foco
        if focus_previous_month:
            # Mês anterior fechado (ex: se estamos em setembro, pega agosto)
            current_date = datetime.now()
            if current_date.month == 1:
                # Janeiro -> pega dezembro do ano anterior
                start_date = datetime(current_date.year - 1, 12, 1)
                end_date = datetime(current_date.year, 1, 1) - timedelta(days=1)
            else:
                # Outros meses -> pega mês anterior
                start_date = datetime(current_date.year, current_date.month - 1, 1)
                if current_date.month == 12:
                    end_date = datetime(current_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(current_date.year, current_date.month, 1) - timedelta(days=1)

            print(f"[ANALYZER] Período mês anterior: {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')}")
        else:
            # Método original (últimos N dias)
            cutoff_date = datetime.now() - timedelta(days=period_days)
            start_date = cutoff_date
            end_date = datetime.now()
            print(f"[ANALYZER] Período últimos {period_days} dias: {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')}")

        filtered_leads = []

        for lead in leads:
            data_cad = lead.get('data_cad')
            if data_cad:
                try:
                    # Tenta diferentes formatos de data
                    lead_date = None
                    date_formats = [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                        "%d/%m/%Y %H:%M:%S",
                        "%d/%m/%Y"
                    ]

                    for fmt in date_formats:
                        try:
                            lead_date = datetime.strptime(data_cad, fmt)
                            break
                        except ValueError:
                            continue

                    if lead_date and start_date <= lead_date <= end_date:
                        filtered_leads.append(lead)

                except Exception:
                    # Se erro na data, inclui para ser conservador
                    filtered_leads.append(lead)
            else:
                # Se não tem data, inclui
                filtered_leads.append(lead)

        return filtered_leads

    def get_monthly_summary(self, leads: List[Dict], focus_previous_month: bool = True) -> Dict[str, Any]:
        """Retorna resumo mensal focado no mês anterior fechado"""

        # Prioriza mês anterior fechado para análise mais precisa
        print(f"[ANALYZER] Iniciando análise com {len(leads)} leads totais")
        recent_leads = self.filter_leads_by_period(leads, period_days=30, focus_previous_month=focus_previous_month)
        print(f"[ANALYZER] Após filtro: {len(recent_leads)} leads do período")

        # Define período para exibição
        period_label = "Mês anterior fechado" if focus_previous_month else "Últimos 30 dias"

        if not recent_leads:
            return {
                "periodo": period_label,
                "total_leads": 0,
                "vendas": 0,
                "reservas": 0,
                "em_negociacao": 0,
                "message": "Nenhum lead encontrado no período"
            }

        # Contadores principais
        total_leads = len(recent_leads)
        vendas = 0
        reservas = 0
        em_negociacao = 0

        # Análise por situação
        for lead in recent_leads:
            situacao = str(lead.get('situacao', '')).upper()

            if any(term in situacao for term in ['VENDA', 'VENDIDO', 'SOLD']):
                vendas += 1
            elif 'RESERVA' in situacao:
                reservas += 1
            elif any(term in situacao for term in ['NEGOCIAÇÃO', 'NEGOCIACAO', 'FOLLOW', 'ATENDIMENTO', 'CONTATO']):
                em_negociacao += 1

        # Top origens
        origens_count = {}
        for lead in recent_leads:
            origem = self.normalize_origem_name(lead.get('origem_nome', 'N/A'))
            origens_count[origem] = origens_count.get(origem, 0) + 1

        top_origens = sorted(origens_count.items(), key=lambda x: x[1], reverse=True)[:3]

        # Taxa de conversão
        taxa_vendas = round((vendas / total_leads) * 100, 2) if total_leads > 0 else 0
        taxa_reservas = round((reservas / total_leads) * 100, 2) if total_leads > 0 else 0

        try:
            return {
                "periodo": period_label,
                "total_leads": total_leads,
                "vendas": vendas,
                "reservas": reservas,
                "em_negociacao": em_negociacao,
                "taxa_vendas": taxa_vendas,
                "taxa_reservas": taxa_reservas,
                "top_origens": top_origens,
                "data_analise": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
        except Exception as e:
            return {
                "periodo": period_label,
                "total_leads": total_leads,
                "vendas": vendas,
                "reservas": reservas,
                "em_negociacao": em_negociacao,
                "taxa_vendas": 0.0,
                "taxa_reservas": 0.0,
                "top_origens": [],
                "data_analise": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "error": str(e)
            }
    
    def analyze_comprehensive(self, leads: List[Dict]) -> Dict[str, Any]:
        """Análise abrangente comparável ao Power BI"""
        
        if not leads:
            return {"error": "Nenhum lead para análise"}
        
        # Filtra por período (últimos 30 dias como exemplo)
        recent_leads = self.filter_leads_by_period(leads, period_days=30)
        
        df = pd.DataFrame(leads)
        df_recent = pd.DataFrame(recent_leads) if recent_leads else pd.DataFrame()
        
        analysis = {
            "overview": {
                "total_leads_base": len(leads),
                "leads_periodo_recente": len(recent_leads),
                "periodo_analise": "Últimos 30 dias",
                "data_analise": datetime.now().strftime("%d/%m/%Y %H:%M")
            },
            "leads_novos": {
                "total": len(recent_leads),
                "comparacao_powerbi": 936,  # Valor de referência
                "diferenca_percentual": round(((len(recent_leads) - 936) / 936) * 100, 2) if len(recent_leads) > 0 else -100
            }
        }
        
        if len(df_recent) > 0:
            # Análise por responsável (padronizado)
            responsaveis_analysis = self._analyze_responsaveis(df_recent)
            analysis["responsaveis"] = responsaveis_analysis
            
            # Análise por origem (padronizada)
            origens_analysis = self._analyze_origens(df_recent)
            analysis["origens"] = origens_analysis
            
            # Análise por situação
            situacoes_analysis = self._analyze_situacoes(df_recent)
            analysis["situacoes"] = situacoes_analysis
            
            # Métricas de conversão
            conversoes_analysis = self._analyze_conversoes(df_recent)
            analysis["conversoes"] = conversoes_analysis
        
        return analysis
    
    def _analyze_responsaveis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa responsáveis com nomes padronizados"""
        
        # CORREÇÃO: Campos reais da API identificados
        responsavel_fields = ['corretor_ultimo', 'gestor', 'corretor', 'responsavel', 'vendedor']
        
        best_field = None
        best_data = None
        
        for field in responsavel_fields:
            if field in df.columns:
                field_data = df[field].dropna()
                if len(field_data) > 0:
                    best_field = field
                    best_data = field_data
                    break
        
        if best_data is None:
            return {"error": "Nenhum campo de responsável encontrado"}
        
        # Normaliza nomes
        normalized_names = best_data.apply(self.normalize_responsavel_name)
        responsaveis_count = normalized_names.value_counts()
        
        # Compara com Power BI
        powerbi_ref = {"Lucia AL": 384, "Luana AL": 256, "Vagner F": 119}
        
        comparison = {}
        for sdr, count_pb in powerbi_ref.items():
            count_nossa = responsaveis_count.get(sdr, 0)
            comparison[sdr] = {
                "power_bi": count_pb,
                "nossa_analise": count_nossa,
                "diferenca": count_nossa - count_pb
            }
        
        return {
            "field_usado": best_field,
            "top_responsaveis": dict(responsaveis_count.head(10)),
            "comparacao_powerbi": comparison,
            "total_com_responsavel": len(best_data)
        }
    
    def _analyze_origens(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa origens com nomes padronizados"""
        
        origem_field = 'origem_nome' if 'origem_nome' in df.columns else 'origem'
        
        if origem_field not in df.columns:
            return {"error": "Campo de origem não encontrado"}
        
        # Normaliza origens
        origem_data = df[origem_field].dropna()
        normalized_origens = origem_data.apply(self.normalize_origem_name)
        origens_count = normalized_origens.value_counts()
        
        # Compara com Power BI
        powerbi_ref = {
            "Facebook": 495, 
            "Instagram": 279, 
            "Meta Org": 45,
            "WhatsApp": 54,
            "Ugello": 7,
            "Portal": 2
        }
        
        comparison = {}
        for origem, count_pb in powerbi_ref.items():
            count_nossa = origens_count.get(origem, 0)
            comparison[origem] = {
                "power_bi": count_pb,
                "nossa_analise": count_nossa,
                "diferenca": count_nossa - count_pb
            }
        
        return {
            "top_origens": dict(origens_count.head(10)),
            "comparacao_powerbi": comparison,
            "total_com_origem": len(origem_data)
        }
    
    def _analyze_situacoes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa situações dos leads"""
        
        if 'situacao' not in df.columns:
            return {"error": "Campo situacao não encontrado"}
        
        situacoes = df['situacao'].value_counts()
        
        # Categoriza situações
        vendas = 0
        reservas = 0
        em_atendimento = 0
        
        for situacao, count in situacoes.items():
            situacao_lower = str(situacao).lower()
            
            if any(word in situacao_lower for word in ['venda', 'vendido', 'sold']):
                vendas += count
            elif 'reserva' in situacao_lower:
                reservas += count
            elif any(word in situacao_lower for word in ['atendimento', 'contato', 'follow']):
                em_atendimento += count
        
        total = len(df)
        
        return {
            "distribuicao": dict(situacoes.head(10)),
            "metricas": {
                "vendas": {"total": vendas, "percentual": round((vendas/total)*100, 2)},
                "reservas": {"total": reservas, "percentual": round((reservas/total)*100, 2)},
                "em_atendimento": {"total": em_atendimento, "percentual": round((em_atendimento/total)*100, 2)}
            }
        }
    
    def _analyze_conversoes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa conversões e métricas de performance"""
        
        total_leads = len(df)
        
        # Calcula conversões por situação
        if 'situacao' not in df.columns:
            return {"error": "Campo situacao necessário para análise de conversões"}
        
        vendas = df[df['situacao'].str.contains('VENDA|VENDIDO', na=False, case=False)]
        reservas = df[df['situacao'].str.contains('RESERVA', na=False, case=False)]
        
        taxa_conversao_vendas = (len(vendas) / total_leads) * 100 if total_leads > 0 else 0
        taxa_conversao_reservas = (len(reservas) / total_leads) * 100 if total_leads > 0 else 0
        
        return {
            "vendas": {
                "total": len(vendas),
                "taxa": round(taxa_conversao_vendas, 2)
            },
            "reservas": {
                "total": len(reservas), 
                "taxa": round(taxa_conversao_reservas, 2)
            },
            "taxa_conversao_total": round(taxa_conversao_vendas + taxa_conversao_reservas, 2)
        }

def create_corrected_analyzer() -> CorrectedCVDWAnalyzer:
    """Factory para criar analisador corrigido"""
    return CorrectedCVDWAnalyzer()