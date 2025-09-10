"""
Complete Daily Cache CVDW - Coleta COMPLETA uma vez por dia
Coleta TODOS os 70.871 leads com TODOS os 75 campos + campos adicionais
Rotinas de limpeza automática às 00:00 e 23:00
"""
import json
import os
import sqlite3
import pandas as pd
import threading
import schedule
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class CVDWCompleteDailyCache:
    """Cache diário com coleta COMPLETA da base CVDW"""
    
    def __init__(self, cache_dir: str = "complete_daily_cache"):
        """Inicializa cache completo diário"""
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Credenciais
        self.email = os.getenv('CVCRM_EMAIL')
        self.token = os.getenv('CVCRM_TOKEN')
        
        if not self.email or not self.token:
            raise ValueError("Email e token CVCRM são obrigatórios no .env")
        
        # Configurações da API
        self.base_url = "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw"
        self.headers = {
            "email": self.email,
            "token": self.token,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Base de dados SQLite otimizada
        self.db_file = self.cache_dir / "cvdw_complete_daily.db"
        self.metadata_file = self.cache_dir / "complete_metadata.json"
        
        # Data atual
        self.today = date.today().isoformat()
        
        # Inicializa sistema
        self._init_database()
        self.metadata = self._load_metadata()
        self._setup_scheduled_tasks()
        
        print(f"[COMPLETE_CACHE] Sistema inicializado para {self.today}")
        print(f"[COMPLETE_CACHE] Target: ~70.871 leads com 75+ campos cada")
    
    def _init_database(self):
        """Inicializa base de dados SQLite otimizada"""
        
        with sqlite3.connect(self.db_file) as conn:
            # Tabela principal de leads
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_leads (
                    id INTEGER PRIMARY KEY,
                    date_cached TEXT NOT NULL,
                    idlead INTEGER,
                    lead_data TEXT NOT NULL,
                    additional_fields_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de campos adicionais (normalized)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_additional_fields (
                    id INTEGER PRIMARY KEY,
                    date_cached TEXT NOT NULL,
                    idlead INTEGER,
                    field_name TEXT,
                    field_value TEXT,
                    field_type TEXT,
                    idcampo INTEGER,
                    reference_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de metadados da coleta
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_collection_log (
                    date TEXT PRIMARY KEY,
                    total_leads_collected INTEGER,
                    total_additional_fields INTEGER,
                    collection_start TIMESTAMP,
                    collection_end TIMESTAMP,
                    pages_processed INTEGER,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            # Índices para performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_leads_date ON daily_leads(date_cached)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_leads_idlead ON daily_leads(idlead)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_additional_date ON daily_additional_fields(date_cached)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_additional_idlead ON daily_additional_fields(idlead)')
            
            # Configurações SQLite para performance
            conn.execute('PRAGMA journal_mode = WAL')
            conn.execute('PRAGMA synchronous = NORMAL')
            conn.execute('PRAGMA cache_size = 10000')
    
    def _load_metadata(self) -> Dict:
        """Carrega metadados"""
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "current_date": self.today,
            "last_complete_collection": None,
            "total_leads_cached": 0,
            "total_additional_fields": 0,
            "collection_status": "pending",
            "estimated_collection_time": "15-20 minutos",
            "auto_cleanup_enabled": True,
            "cleanup_schedule": ["00:00", "23:00"]
        }
    
    def _save_metadata(self):
        """Salva metadados"""
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def has_complete_data_today(self) -> bool:
        """Verifica se já temos coleta completa para hoje"""
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute(
                    'SELECT total_leads_collected, status FROM daily_collection_log WHERE date = ?',
                    (self.today,)
                )
                result = cursor.fetchone()
                
                if result and result[1] == 'completed' and result[0] > 0:
                    print(f"[COMPLETE_CACHE] Coleta completa já realizada hoje: {result[0]} leads")
                    return True
                
            return False
            
        except Exception as e:
            print(f"[COMPLETE_CACHE] Erro ao verificar dados: {str(e)}")
            return False
    
    def collect_all_leads(self) -> Dict[str, Any]:
        """Coleta TODOS os leads da API CVDW"""
        
        if self.has_complete_data_today():
            return {"status": "already_collected", "message": "Dados já coletados hoje"}
        
        print(f"[COMPLETE_CACHE] INICIANDO COLETA COMPLETA - {datetime.now()}")
        start_time = datetime.now()
        
        # Registra início da coleta
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO daily_collection_log 
                (date, collection_start, status) VALUES (?, ?, ?)
            ''', (self.today, start_time.isoformat(), 'in_progress'))
        
        total_leads_collected = 0
        total_additional_fields = 0
        pages_processed = 0
        
        try:
            # Primeira requisição para descobrir total de páginas
            print("[COMPLETE_CACHE] Descobrindo total de dados disponíveis...")
            
            response = requests.get(
                f"{self.base_url}/leads",
                headers=self.headers,
                params={"registros_por_pagina": 500, "pagina": 1},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API erro: {response.status_code} - {response.text}")
            
            first_data = response.json()
            total_records = first_data.get('total_de_registros', 0)
            total_pages = first_data.get('total_de_paginas', 0)
            
            print(f"[COMPLETE_CACHE] Descoberto: {total_records} leads em {total_pages} páginas")
            
            # Processa primeira página
            if 'dados' in first_data:
                self._store_page_data(first_data['dados'], self.today)
                total_leads_collected += len(first_data['dados'])
                total_additional_fields += self._count_additional_fields(first_data['dados'])
                pages_processed = 1
                
                print(f"[COMPLETE_CACHE] Página 1/{total_pages} processada ({len(first_data['dados'])} leads)")
            
            # Processa páginas restantes
            for page in range(2, total_pages + 1):
                try:
                    # Rate limiting inteligente
                    if page % 10 == 0:
                        time.sleep(3)  # Pausa maior a cada 10 páginas
                    else:
                        time.sleep(1)  # Pausa padrão
                    
                    response = requests.get(
                        f"{self.base_url}/leads",
                        headers=self.headers,
                        params={"registros_por_pagina": 500, "pagina": page},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        page_data = response.json()
                        
                        if 'dados' in page_data and page_data['dados']:
                            self._store_page_data(page_data['dados'], self.today)
                            page_leads = len(page_data['dados'])
                            page_additional = self._count_additional_fields(page_data['dados'])
                            
                            total_leads_collected += page_leads
                            total_additional_fields += page_additional
                            pages_processed = page
                            
                            if page % 25 == 0 or page == total_pages:  # Progress report
                                elapsed = datetime.now() - start_time
                                print(f"[COMPLETE_CACHE] Progresso: {page}/{total_pages} páginas | "
                                      f"{total_leads_collected} leads | {elapsed}")
                        else:
                            print(f"[COMPLETE_CACHE] Página {page} vazia, finalizando...")
                            break
                            
                    elif response.status_code == 429:  # Rate limit
                        print(f"[COMPLETE_CACHE] Rate limit na página {page}, aguardando...")
                        time.sleep(10)
                        continue
                    else:
                        print(f"[COMPLETE_CACHE] Erro na página {page}: {response.status_code}")
                        continue
                        
                except Exception as e:
                    print(f"[COMPLETE_CACHE] Erro na página {page}: {str(e)}")
                    continue
            
            # Finaliza coleta
            end_time = datetime.now()
            duration = end_time - start_time
            
            # Atualiza log da coleta
            with sqlite3.connect(self.db_file) as conn:
                conn.execute('''
                    UPDATE daily_collection_log SET
                        total_leads_collected = ?,
                        total_additional_fields = ?,
                        collection_end = ?,
                        pages_processed = ?,
                        status = ?
                    WHERE date = ?
                ''', (
                    total_leads_collected,
                    total_additional_fields, 
                    end_time.isoformat(),
                    pages_processed,
                    'completed',
                    self.today
                ))
            
            # Atualiza metadados
            self.metadata.update({
                "last_complete_collection": end_time.isoformat(),
                "total_leads_cached": total_leads_collected,
                "total_additional_fields": total_additional_fields,
                "collection_status": "completed"
            })
            self._save_metadata()
            
            result = {
                "status": "success",
                "total_leads_collected": total_leads_collected,
                "total_additional_fields": total_additional_fields,
                "pages_processed": pages_processed,
                "duration_minutes": round(duration.total_seconds() / 60, 2),
                "collection_date": self.today
            }
            
            print(f"[COMPLETE_CACHE] COLETA CONCLUÍDA!")
            print(f"  - Leads coletados: {total_leads_collected}")
            print(f"  - Campos adicionais: {total_additional_fields}")
            print(f"  - Páginas processadas: {pages_processed}")
            print(f"  - Duração: {result['duration_minutes']} minutos")
            
            return result
            
        except Exception as e:
            # Registra erro
            with sqlite3.connect(self.db_file) as conn:
                conn.execute('''
                    UPDATE daily_collection_log SET
                        status = ?,
                        error_message = ?,
                        total_leads_collected = ?,
                        pages_processed = ?
                    WHERE date = ?
                ''', ('error', str(e), total_leads_collected, pages_processed, self.today))
            
            print(f"[COMPLETE_CACHE] ERRO na coleta: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "partial_leads_collected": total_leads_collected,
                "pages_processed": pages_processed
            }
    
    def _store_page_data(self, leads: List[Dict], date_cached: str):
        """Armazena dados de uma página na base"""
        
        with sqlite3.connect(self.db_file) as conn:
            for lead in leads:
                # Dados principais do lead
                lead_json = json.dumps(lead, ensure_ascii=False, default=str)
                additional_count = len(lead.get('campos_adicionais', []))
                
                conn.execute('''
                    INSERT INTO daily_leads 
                    (date_cached, idlead, lead_data, additional_fields_count)
                    VALUES (?, ?, ?, ?)
                ''', (date_cached, lead.get('idlead'), lead_json, additional_count))
                
                # Campos adicionais (normalized)
                for campo in lead.get('campos_adicionais', []):
                    conn.execute('''
                        INSERT INTO daily_additional_fields
                        (date_cached, idlead, field_name, field_value, field_type, idcampo, reference_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date_cached,
                        lead.get('idlead'),
                        campo.get('nome'),
                        campo.get('valor'),
                        campo.get('tipo'),
                        campo.get('idcampo'),
                        campo.get('referencia_data')
                    ))
    
    def _count_additional_fields(self, leads: List[Dict]) -> int:
        """Conta campos adicionais em uma lista de leads"""
        
        return sum(len(lead.get('campos_adicionais', [])) for lead in leads)
    
    def get_complete_leads(self) -> Optional[List[Dict]]:
        """Retorna todos os leads do cache diário"""
        
        if not self.has_complete_data_today():
            return None
        
        try:
            leads = []
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute(
                    'SELECT lead_data FROM daily_leads WHERE date_cached = ? ORDER BY idlead',
                    (self.today,)
                )
                
                for (lead_json,) in cursor:
                    lead = json.loads(lead_json)
                    leads.append(lead)
            
            print(f"[COMPLETE_CACHE] Retornados {len(leads)} leads do cache completo")
            return leads
            
        except Exception as e:
            print(f"[COMPLETE_CACHE] Erro ao recuperar leads: {str(e)}")
            return None
    
    def get_leads_dataframe(self) -> Optional[pd.DataFrame]:
        """Retorna DataFrame completo otimizado para análise"""
        
        leads = self.get_complete_leads()
        if not leads:
            return None
        
        try:
            df = pd.DataFrame(leads)
            
            # Otimizações para análise
            date_columns = [
                'data_cad', 'data_ultima_alteracao', 'data_ultima_interacao',
                'data_associacao_corretor', 'data_primeira_interacao_corretor',
                'data_primeira_interacao_gestor', 'data_reativacao', 
                'data_cancelamento', 'data_vencimento', 'ultima_data_conversao'
            ]
            
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Normaliza campos de texto
            text_columns = [
                'situacao', 'origem_nome', 'nome', 'empreendimento',
                'corretor', 'gestor', 'midia_original'
            ]
            
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].fillna('NAO_INFORMADO')
            
            # Campos numéricos
            numeric_columns = ['score', 'possibilidade_venda', 'reserva']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            print(f"[COMPLETE_CACHE] DataFrame criado: {len(df)} x {len(df.columns)}")
            return df
            
        except Exception as e:
            print(f"[COMPLETE_CACHE] Erro ao criar DataFrame: {str(e)}")
            return None
    
    def get_additional_fields_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos campos adicionais coletados"""
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Total de campos adicionais
                cursor = conn.execute(
                    'SELECT COUNT(*) FROM daily_additional_fields WHERE date_cached = ?',
                    (self.today,)
                )
                total_fields = cursor.fetchone()[0]
                
                # Campos únicos
                cursor = conn.execute(
                    'SELECT field_name, COUNT(*) as count FROM daily_additional_fields WHERE date_cached = ? GROUP BY field_name ORDER BY count DESC',
                    (self.today,)
                )
                field_counts = cursor.fetchall()
                
                # Leads com campos adicionais
                cursor = conn.execute(
                    'SELECT COUNT(DISTINCT idlead) FROM daily_additional_fields WHERE date_cached = ?',
                    (self.today,)
                )
                leads_with_fields = cursor.fetchone()[0]
            
            return {
                "total_additional_fields": total_fields,
                "unique_field_types": len(field_counts),
                "leads_with_additional_fields": leads_with_fields,
                "field_distribution": dict(field_counts[:10])  # Top 10
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _setup_scheduled_tasks(self):
        """Configura rotinas automáticas"""
        
        schedule.every().day.at("00:00").do(self._midnight_cleanup)
        schedule.every().day.at("23:00").do(self._evening_cleanup)
        
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print("[COMPLETE_CACHE] Rotinas automáticas: 00:00 (reset) e 23:00 (limpeza)")
    
    def _run_scheduler(self):
        """Executa scheduler em background"""
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                print(f"[COMPLETE_CACHE] Erro no scheduler: {str(e)}")
                time.sleep(300)
    
    def _midnight_cleanup(self):
        """Rotina 00:00 - Novo dia, reset completo"""
        
        print("[COMPLETE_CACHE] === ROTINA 00:00 - NOVO DIA ===")
        
        # Atualiza data
        self.today = date.today().isoformat()
        
        # Limpa dados antigos
        self.cleanup_old_data()
        
        # Reset metadados
        self.metadata.update({
            "current_date": self.today,
            "last_complete_collection": None,
            "total_leads_cached": 0,
            "total_additional_fields": 0,
            "collection_status": "pending"
        })
        self._save_metadata()
        
        print(f"[COMPLETE_CACHE] Sistema resetado para {self.today}")
    
    def _evening_cleanup(self):
        """Rotina 23:00 - Limpeza preventiva"""
        
        print("[COMPLETE_CACHE] === ROTINA 23:00 - LIMPEZA PREVENTIVA ===")
        
        # Remove apenas dados muito antigos (mantém hoje)
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('DELETE FROM daily_leads WHERE date_cached < ?', (self.today,))
            conn.execute('DELETE FROM daily_additional_fields WHERE date_cached < ?', (self.today,))
            conn.execute('DELETE FROM daily_collection_log WHERE date < ?', (self.today,))
            conn.execute('VACUUM')
    
    def cleanup_old_data(self) -> Dict[str, int]:
        """Limpeza completa de dados antigos"""
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Remove dados antigos
                cursor = conn.execute('DELETE FROM daily_leads WHERE date_cached != ?', (self.today,))
                leads_removed = cursor.rowcount
                
                cursor = conn.execute('DELETE FROM daily_additional_fields WHERE date_cached != ?', (self.today,))
                fields_removed = cursor.rowcount
                
                cursor = conn.execute('DELETE FROM daily_collection_log WHERE date != ?', (self.today,))
                logs_removed = cursor.rowcount
                
                # Compacta base
                conn.execute('VACUUM')
            
            print(f"[COMPLETE_CACHE] Limpeza: {leads_removed} leads, {fields_removed} campos adicionais removidos")
            
            return {
                "leads_removed": leads_removed,
                "fields_removed": fields_removed,
                "logs_removed": logs_removed
            }
            
        except Exception as e:
            print(f"[COMPLETE_CACHE] Erro na limpeza: {str(e)}")
            return {"error": str(e)}
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Status completo do cache"""
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Dados de hoje
                cursor = conn.execute(
                    'SELECT total_leads_collected, total_additional_fields, status, collection_start, collection_end FROM daily_collection_log WHERE date = ?',
                    (self.today,)
                )
                today_log = cursor.fetchone()
                
                # Tamanho da base
                cursor = conn.execute('SELECT COUNT(*) FROM daily_leads WHERE date_cached = ?', (self.today,))
                cached_leads = cursor.fetchone()[0]
                
                db_size_mb = self.db_file.stat().st_size / (1024 * 1024) if self.db_file.exists() else 0
            
            status = {
                "current_date": self.today,
                "has_complete_data": today_log is not None and today_log[2] == 'completed',
                "cached_leads": cached_leads,
                "database_size_mb": round(db_size_mb, 2),
                "auto_cleanup_schedule": ["00:00", "23:00"]
            }
            
            if today_log:
                status.update({
                    "total_leads_collected": today_log[0] or 0,
                    "total_additional_fields": today_log[1] or 0,
                    "collection_status": today_log[2],
                    "collection_start": today_log[3],
                    "collection_end": today_log[4]
                })
                
                if today_log[3] and today_log[4]:
                    start = datetime.fromisoformat(today_log[3])
                    end = datetime.fromisoformat(today_log[4])
                    duration = end - start
                    status["collection_duration_minutes"] = round(duration.total_seconds() / 60, 2)
            
            return status
            
        except Exception as e:
            return {"error": str(e)}


def create_complete_daily_cache(cache_dir: str = "complete_daily_cache") -> CVDWCompleteDailyCache:
    """Factory function para criar cache diário completo"""
    return CVDWCompleteDailyCache(cache_dir)