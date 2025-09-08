"""
Analisador Avançado CVDW - Contexto inteligente para análise de dados
"""
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from utils.helpers import parse_date, format_number, calculate_conversion_rate

class CVDWAnalyzer:
    """Analisador avançado para dados CVDW com contexto empresarial"""
    
    def __init__(self):
        """Inicializa analisador"""
        
        # Contexto da BP Incorporadora
        self.company_context = {
            "name": "BP Incorporadora",
            "business": "Incorporação Imobiliária",
            "target_audience": "Compradores de imóveis",
            "main_channels": ["Facebook", "WhatsApp", "Google Ads", "Mídia Paga", "ChatBot"],
            "key_metrics": ["CPL", "Taxa de Conversão", "ROI", "Vendas", "Reservas"]
        }
        
        # Mapeamento de situações importantes
        self.status_mapping = {
            "conversion": ["VENDA REALIZADA", "VENDIDO", "FECHADO"],
            "hot_leads": ["RESERVA", "EM NEGOCIACAO", "PROPOSTA"],
            "nurturing": ["ATENDIMENTO CORRETOR", "EM ANDAMENTO", "QUALIFICADO"],
            "cold": ["DESISTIU", "NAO INTERESSADO", "PERDIDO"],
            "follow_up": ["REAGENDADO", "PENDENTE", "AGUARDANDO"]
        }
        
        # Contexto temporal para análises
        self.temporal_context = {
            "campaign_cycles": 30,  # dias
            "sales_cycle": 45,      # dias médios para conversão
            "hot_lead_window": 7,   # dias para considerar lead quente
            "follow_up_max": 30     # dias máximos sem follow-up
        }
    
    def analyze_comprehensive(self, leads: List[Dict]) -> Dict[str, Any]:
        """Análise abrangente com contexto empresarial"""
        
        if not leads:
            return {"error": "Nenhum dado para análise"}
        
        df = pd.DataFrame(leads)
        analysis = {
            "overview": self._analyze_overview(df),
            "performance": self._analyze_performance(df),
            "channels": self._analyze_channels(df),
            "temporal": self._analyze_temporal(df),
            "quality": self._analyze_quality(df),
            "insights": self._generate_business_insights(df),
            "recommendations": self._generate_recommendations(df)
        }
        
        return analysis
    
    def _analyze_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise geral dos dados"""
        
        total = len(df)
        
        # Conversões por tipo
        conversions = self._count_by_status_type(df, "conversion")
        hot_leads = self._count_by_status_type(df, "hot_leads")
        nurturing = self._count_by_status_type(df, "nurturing")
        cold = self._count_by_status_type(df, "cold")
        
        return {
            "total_leads": total,
            "conversions": {
                "count": conversions,
                "rate": round((conversions / total) * 100, 2) if total > 0 else 0
            },
            "hot_leads": {
                "count": hot_leads,
                "rate": round((hot_leads / total) * 100, 2) if total > 0 else 0
            },
            "pipeline": {
                "nurturing": nurturing,
                "cold": cold,
                "total_active": hot_leads + nurturing
            },
            "health_score": self._calculate_health_score(conversions, hot_leads, total)
        }
    
    def _analyze_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise de performance por responsável"""
        
        performance = {}
        
        # Analisa diferentes campos de responsável
        responsavel_fields = ["corretor", "responsavel", "gestor", "vendedor"]
        
        for field in responsavel_fields:
            if field in df.columns and df[field].notna().any():
                perf_data = self._analyze_responsavel_performance(df, field)
                if perf_data:
                    performance[field] = perf_data
                    break
        
        return performance
    
    def _analyze_responsavel_performance(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """Análise detalhada por responsável"""
        
        # Remove vazios
        df_clean = df[df[field].notna() & (df[field] != "")]
        
        if len(df_clean) == 0:
            return {}
        
        # Agrupa por responsável
        responsavel_stats = []
        
        for responsavel in df_clean[field].unique():
            responsavel_df = df_clean[df_clean[field] == responsavel]
            total_leads = len(responsavel_df)
            
            conversions = self._count_by_status_type(responsavel_df, "conversion")
            hot_leads = self._count_by_status_type(responsavel_df, "hot_leads")
            
            responsavel_stats.append({
                "name": responsavel,
                "total_leads": total_leads,
                "conversions": conversions,
                "conversion_rate": round((conversions / total_leads) * 100, 2) if total_leads > 0 else 0,
                "hot_leads": hot_leads,
                "pipeline_strength": round(((hot_leads + conversions) / total_leads) * 100, 2) if total_leads > 0 else 0
            })
        
        # Ordena por performance
        responsavel_stats.sort(key=lambda x: x['conversion_rate'], reverse=True)
        
        return {
            "field_name": field,
            "total_responsaveis": len(responsavel_stats),
            "top_performers": responsavel_stats[:5],
            "average_conversion_rate": round(sum(r['conversion_rate'] for r in responsavel_stats) / len(responsavel_stats), 2) if responsavel_stats else 0
        }
    
    def _analyze_channels(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise de performance por canal"""
        
        origem_field = "origem_nome" if "origem_nome" in df.columns else "origem"
        
        if origem_field not in df.columns:
            return {"error": "Campo de origem não encontrado"}
        
        channel_stats = []
        
        for canal in df[origem_field].value_counts().index[:10]:  # Top 10
            canal_df = df[df[origem_field] == canal]
            total_leads = len(canal_df)
            
            conversions = self._count_by_status_type(canal_df, "conversion")
            hot_leads = self._count_by_status_type(canal_df, "hot_leads")
            cold = self._count_by_status_type(canal_df, "cold")
            
            channel_stats.append({
                "channel": canal,
                "total_leads": total_leads,
                "conversions": conversions,
                "conversion_rate": round((conversions / total_leads) * 100, 2) if total_leads > 0 else 0,
                "hot_leads": hot_leads,
                "cold_rate": round((cold / total_leads) * 100, 2) if total_leads > 0 else 0,
                "roi_indicator": self._calculate_channel_roi_indicator(conversions, total_leads, canal)
            })
        
        # Ordena por ROI indicator
        channel_stats.sort(key=lambda x: x['roi_indicator'], reverse=True)
        
        return {
            "total_channels": len(channel_stats),
            "best_performers": channel_stats[:5],
            "total_leads_by_channel": {stat['channel']: stat['total_leads'] for stat in channel_stats}
        }
    
    def _analyze_temporal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise temporal dos dados"""
        
        if 'data_cad' not in df.columns:
            return {"error": "Campo de data não encontrado"}
        
        # Converte datas
        df_copy = df.copy()
        df_copy['data_parsed'] = df_copy['data_cad'].apply(parse_date)
        df_valid_dates = df_copy[df_copy['data_parsed'].notna()]
        
        if len(df_valid_dates) == 0:
            return {"error": "Nenhuma data válida encontrada"}
        
        df_valid_dates = df_valid_dates.sort_values('data_parsed')
        
        # Análise por período
        now = datetime.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        recent_leads = df_valid_dates[df_valid_dates['data_parsed'] >= last_30_days]
        very_recent = df_valid_dates[df_valid_dates['data_parsed'] >= last_7_days]
        
        return {
            "date_range": {
                "start": df_valid_dates['data_parsed'].min().strftime('%Y-%m-%d'),
                "end": df_valid_dates['data_parsed'].max().strftime('%Y-%m-%d'),
                "total_days": (df_valid_dates['data_parsed'].max() - df_valid_dates['data_parsed'].min()).days
            },
            "recent_activity": {
                "last_30_days": len(recent_leads),
                "last_7_days": len(very_recent),
                "daily_average": round(len(recent_leads) / 30, 1),
                "trend": self._calculate_trend(df_valid_dates)
            },
            "seasonal_patterns": self._analyze_seasonal_patterns(df_valid_dates)
        }
    
    def _analyze_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise de qualidade dos dados"""
        
        total = len(df)
        quality_metrics = {}
        
        # Campos essenciais
        essential_fields = ["nome", "situacao", "origem_nome", "data_cad", "email", "telefone"]
        
        for field in essential_fields:
            if field in df.columns:
                non_empty = df[field].notna() & (df[field] != "")
                coverage = (non_empty.sum() / total) * 100
                quality_metrics[field] = {
                    "coverage": round(coverage, 1),
                    "missing": total - non_empty.sum()
                }
        
        # Score geral de qualidade
        avg_coverage = sum(m["coverage"] for m in quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0
        
        quality_score = "Excelente" if avg_coverage >= 90 else "Boa" if avg_coverage >= 75 else "Regular" if avg_coverage >= 60 else "Baixa"
        
        return {
            "overall_score": quality_score,
            "average_coverage": round(avg_coverage, 1),
            "field_analysis": quality_metrics,
            "recommendations": self._get_quality_recommendations(avg_coverage)
        }
    
    def _generate_business_insights(self, df: pd.DataFrame) -> List[str]:
        """Gera insights de negócio contextualizados"""
        
        insights = []
        total = len(df)
        
        # Insight 1: Performance geral
        conversions = self._count_by_status_type(df, "conversion")
        conversion_rate = (conversions / total) * 100 if total > 0 else 0
        
        if conversion_rate > 15:
            insights.append(f"Excelente taxa de conversão: {conversion_rate:.1f}% (acima da média do setor)")
        elif conversion_rate > 8:
            insights.append(f"Taxa de conversão saudável: {conversion_rate:.1f}% (dentro da média)")
        else:
            insights.append(f"Taxa de conversão baixa: {conversion_rate:.1f}% - oportunidade de melhoria")
        
        # Insight 2: Canal mais efetivo
        if "origem_nome" in df.columns or "origem" in df.columns:
            origem_field = "origem_nome" if "origem_nome" in df.columns else "origem"
            top_channel = df[origem_field].value_counts().index[0]
            top_count = df[origem_field].value_counts().iloc[0]
            
            insights.append(f"Canal principal: '{top_channel}' com {top_count} leads ({(top_count/total)*100:.1f}%)")
        
        # Insight 3: Pipeline
        hot_leads = self._count_by_status_type(df, "hot_leads")
        nurturing = self._count_by_status_type(df, "nurturing")
        
        pipeline_strength = ((hot_leads + nurturing) / total) * 100 if total > 0 else 0
        
        if pipeline_strength > 40:
            insights.append(f"Pipeline forte: {pipeline_strength:.1f}% dos leads em negociação/atendimento")
        else:
            insights.append(f"Pipeline precisa de atenção: apenas {pipeline_strength:.1f}% em negociação ativa")
        
        # Insight 4: Qualidade dos dados
        if "email" in df.columns:
            email_coverage = (df["email"].notna().sum() / total) * 100
            if email_coverage < 70:
                insights.append(f"Atenção: apenas {email_coverage:.1f}% dos leads têm email cadastrado")
        
        return insights
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Gera recomendações acionáveis"""
        
        recommendations = []
        total = len(df)
        
        # Recomendação 1: Conversão
        conversions = self._count_by_status_type(df, "conversion")
        conversion_rate = (conversions / total) * 100 if total > 0 else 0
        
        if conversion_rate < 8:
            recommendations.append("Implementar processo de qualificação de leads mais rigoroso")
            recommendations.append("Analisar e otimizar o follow-up de leads em atendimento")
        
        # Recomendação 2: Follow-up
        nurturing = self._count_by_status_type(df, "nurturing")
        if nurturing > total * 0.3:
            recommendations.append("Acelerar processo de follow-up - muitos leads em atendimento")
        
        # Recomendação 3: Canais
        if "origem_nome" in df.columns or "origem" in df.columns:
            origem_field = "origem_nome" if "origem_nome" in df.columns else "origem"
            
            # Analisa performance por canal
            channel_performance = {}
            for canal in df[origem_field].value_counts().index[:5]:
                canal_df = df[df[origem_field] == canal]
                canal_conversions = self._count_by_status_type(canal_df, "conversion")
                canal_rate = (canal_conversions / len(canal_df)) * 100 if len(canal_df) > 0 else 0
                channel_performance[canal] = canal_rate
            
            best_channel = max(channel_performance.items(), key=lambda x: x[1])
            worst_channel = min(channel_performance.items(), key=lambda x: x[1])
            
            if best_channel[1] > worst_channel[1] * 2:
                recommendations.append(f"Priorizar investimento no canal '{best_channel[0]}' (taxa: {best_channel[1]:.1f}%)")
                recommendations.append(f"Revisar estratégia do canal '{worst_channel[0]}' (taxa: {worst_channel[1]:.1f}%)")
        
        # Recomendação 4: Qualidade de dados
        if "email" in df.columns:
            email_coverage = (df["email"].notna().sum() / total) * 100
            if email_coverage < 80:
                recommendations.append("Implementar campos obrigatórios para captura de email e telefone")
        
        return recommendations[:5]  # Limita a 5 recomendações principais
    
    # Métodos auxiliares
    
    def _count_by_status_type(self, df: pd.DataFrame, status_type: str) -> int:
        """Conta leads por tipo de status"""
        
        if "situacao" not in df.columns:
            return 0
        
        status_list = self.status_mapping.get(status_type, [])
        count = 0
        
        for status in status_list:
            count += df["situacao"].str.contains(status, case=False, na=False).sum()
        
        return count
    
    def _calculate_health_score(self, conversions: int, hot_leads: int, total: int) -> str:
        """Calcula score de saúde do pipeline"""
        
        if total == 0:
            return "Insuficiente"
        
        active_rate = ((conversions + hot_leads) / total) * 100
        
        if active_rate >= 25:
            return "Excelente"
        elif active_rate >= 15:
            return "Bom"
        elif active_rate >= 8:
            return "Regular"
        else:
            return "Precisa Melhoria"
    
    def _calculate_channel_roi_indicator(self, conversions: int, total_leads: int, channel: str) -> float:
        """Calcula indicador de ROI por canal (simplificado)"""
        
        if total_leads == 0:
            return 0
        
        conversion_rate = conversions / total_leads
        
        # Pesos baseados no custo típico por canal
        channel_weights = {
            "Google Ads": 0.8,  # Mais caro
            "Facebook": 0.9,
            "Instagram": 0.9,
            "WhatsApp": 1.2,    # Mais barato
            "Indicação": 1.5,   # Muito barato
            "ChatBot": 1.3
        }
        
        weight = channel_weights.get(channel, 1.0)
        return conversion_rate * weight * 100
    
    def _calculate_trend(self, df_with_dates: pd.DataFrame) -> str:
        """Calcula tendência dos últimos 30 dias"""
        
        now = datetime.now()
        last_30 = now - timedelta(days=30)
        last_15 = now - timedelta(days=15)
        
        first_half = df_with_dates[
            (df_with_dates['data_parsed'] >= last_30) & 
            (df_with_dates['data_parsed'] < last_15)
        ]
        second_half = df_with_dates[df_with_dates['data_parsed'] >= last_15]
        
        if len(first_half) == 0 or len(second_half) == 0:
            return "Insuficiente"
        
        first_daily = len(first_half) / 15
        second_daily = len(second_half) / 15
        
        if second_daily > first_daily * 1.1:
            return "Crescente"
        elif second_daily < first_daily * 0.9:
            return "Decrescente"
        else:
            return "Estável"
    
    def _analyze_seasonal_patterns(self, df_with_dates: pd.DataFrame) -> Dict[str, Any]:
        """Analisa padrões sazonais"""
        
        df_with_dates['month'] = df_with_dates['data_parsed'].dt.month
        df_with_dates['weekday'] = df_with_dates['data_parsed'].dt.weekday
        
        monthly = df_with_dates['month'].value_counts().sort_index()
        weekday = df_with_dates['weekday'].value_counts().sort_index()
        
        weekday_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        return {
            "best_month": monthly.index[0] if len(monthly) > 0 else None,
            "best_weekday": weekday_names[weekday.index[0]] if len(weekday) > 0 else None,
            "monthly_distribution": monthly.to_dict(),
            "weekday_distribution": {weekday_names[k]: v for k, v in weekday.to_dict().items() if k < len(weekday_names)}
        }
    
    def _get_quality_recommendations(self, avg_coverage: float) -> List[str]:
        """Recomendações para melhoria da qualidade dos dados"""
        
        recommendations = []
        
        if avg_coverage < 60:
            recommendations.append("Implementar validação obrigatória de campos essenciais")
            recommendations.append("Treinar equipe para preenchimento completo de dados")
        elif avg_coverage < 80:
            recommendations.append("Revisar formulários de captação para incluir mais campos")
            recommendations.append("Implementar follow-up para completar dados faltantes")
        else:
            recommendations.append("Manter padrão de qualidade atual")
        
        return recommendations

def create_analyzer() -> CVDWAnalyzer:
    """Factory function para criar analisador"""
    return CVDWAnalyzer()