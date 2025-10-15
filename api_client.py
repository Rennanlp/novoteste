"""
Cliente para API de Relatórios Reversos Completo
URL: https://ap5tntnr6b.execute-api.us-east-1.amazonaws.com/api/relatorioreversoscompleto/dini/dfin
"""

import requests
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RelatorioReverso:
    """Estrutura base para dados do relatório reverso"""
    # Campos básicos - adapte conforme a estrutura real da API
    id: Optional[str] = None
    data_relatorio: Optional[date] = None
    codigo_fundo: Optional[str] = None
    nome_fundo: Optional[str] = None
    cnpj: Optional[str] = None
    data_base: Optional[date] = None
    
    # Dados financeiros
    patrimonio_liquido: Optional[float] = None
    ativo_total: Optional[float] = None
    passivo_total: Optional[float] = None
    receitas: Optional[float] = None
    despesas: Optional[float] = None
    resultado_liquido: Optional[float] = None
    
    # Metadados
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None


class APIRelatorioReversoClient:
    """Cliente para consumir a API de Relatórios Reversos"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "https://ap5tntnr6b.execute-api.us-east-1.amazonaws.com"
        self.session = requests.Session()
        
        # Headers padrão
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'RelatorioReversoClient/1.0'
        })
    
    def get_relatorio_completo(self, dini: str = None, dfin: str = None) -> List[RelatorioReverso]:
        """
        Busca relatórios reversos completos
        
        Args:
            dini: Data inicial (formato YYYY-MM-DD)
            dfin: Data final (formato YYYY-MM-DD)
            
        Returns:
            Lista de objetos RelatorioReverso
        """
        endpoint = f"/api/relatorioreversoscompleto/{dini or 'dini'}/{dfin or 'dfin'}"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Fazendo requisição para: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data)
            else:
                logger.error(f"Erro na API: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            raise
    
    def _parse_response(self, data: Any) -> List[RelatorioReverso]:
        """
        Converte resposta da API em objetos RelatorioReverso
        
        Args:
            data: Dados brutos da API
            
        Returns:
            Lista de objetos RelatorioReverso
        """
        relatorios = []
        
        # Se data é uma lista, processa cada item
        if isinstance(data, list):
            for item in data:
                relatorio = self._create_relatorio_from_data(item)
                relatorios.append(relatorio)
        
        # Se data é um objeto único
        elif isinstance(data, dict):
            relatorio = self._create_relatorio_from_data(data)
            relatorios.append(relatorio)
        
        # Se data é um wrapper com lista de relatórios
        elif isinstance(data, dict) and 'relatorios' in data:
            for item in data['relatorios']:
                relatorio = self._create_relatorio_from_data(item)
                relatorios.append(relatorio)
        
        # Se data é um wrapper com dados do relatório
        elif isinstance(data, dict) and 'data' in data:
            relatorio = self._create_relatorio_from_data(data['data'])
            relatorios.append(relatorio)
        
        else:
            logger.warning(f"Formato de resposta não reconhecido: {type(data)}")
            # Tenta criar um relatório com os dados brutos
            relatorio = RelatorioReverso(raw_data=data)
            relatorios.append(relatorio)
        
        return relatorios
    
    def _create_relatorio_from_data(self, data: Dict[str, Any]) -> RelatorioReverso:
        """
        Cria objeto RelatorioReverso a partir dos dados
        
        Args:
            data: Dicionário com dados do relatório
            
        Returns:
            Objeto RelatorioReverso
        """
        relatorio = RelatorioReverso()
        
        # Mapeamento de campos comuns
        field_mapping = {
            'id': ['id', 'ID', 'Id'],
            'codigo_fundo': ['codigo_fundo', 'codigoFundo', 'codigo', 'ticker'],
            'nome_fundo': ['nome_fundo', 'nomeFundo', 'nome', 'name'],
            'cnpj': ['cnpj', 'CNPJ'],
            'patrimonio_liquido': ['patrimonio_liquido', 'patrimonioLiquido', 'patrimonio'],
            'ativo_total': ['ativo_total', 'ativoTotal', 'ativo'],
            'passivo_total': ['passivo_total', 'passivoTotal', 'passivo'],
            'receitas': ['receitas', 'receita', 'receita_total'],
            'despesas': ['despesas', 'despesa', 'despesa_total'],
            'resultado_liquido': ['resultado_liquido', 'resultadoLiquido', 'resultado']
        }
        
        # Mapeamento de datas
        date_fields = ['data_relatorio', 'data_base', 'dataRelatorio', 'dataBase', 'data']
        datetime_fields = ['created_at', 'updated_at', 'createdAt', 'updatedAt']
        
        # Processa campos mapeados
        for attr_name, possible_keys in field_mapping.items():
            for key in possible_keys:
                if key in data:
                    value = data[key]
                    if attr_name in ['patrimonio_liquido', 'ativo_total', 'passivo_total', 
                                   'receitas', 'despesas', 'resultado_liquido']:
                        try:
                            value = float(value) if value is not None else None
                        except (ValueError, TypeError):
                            value = None
                    setattr(relatorio, attr_name, value)
                    break
        
        # Processa campos de data
        for key in date_fields:
            if key in data:
                try:
                    date_value = self._parse_date(data[key])
                    relatorio.data_relatorio = date_value
                    break
                except (ValueError, TypeError):
                    pass
        
        # Processa campos de datetime
        for key in datetime_fields:
            if key in data:
                try:
                    datetime_value = self._parse_datetime(data[key])
                    if 'created' in key.lower():
                        relatorio.created_at = datetime_value
                    elif 'updated' in key.lower():
                        relatorio.updated_at = datetime_value
                except (ValueError, TypeError):
                    pass
        
        # Armazena dados brutos para referência
        relatorio.raw_data = data
        
        return relatorio
    
    def _parse_date(self, date_str: str) -> date:
        """Converte string para objeto date"""
        if isinstance(date_str, date):
            return date_str
        
        # Tenta diferentes formatos de data
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']
        
        for fmt in formats:
            try:
                if 'T' in fmt:
                    return datetime.strptime(date_str, fmt).date()
                else:
                    return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Não foi possível converter '{date_str}' para data")
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Converte string para objeto datetime"""
        if isinstance(datetime_str, datetime):
            return datetime_str
        
        # Tenta diferentes formatos de datetime
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Não foi possível converter '{datetime_str}' para datetime")


# Exemplo de uso
if __name__ == "__main__":
    # Criar cliente
    client = APIRelatorioReversoClient()
    
    try:
        # Buscar relatórios (substitua pelas datas desejadas)
        relatorios = client.get_relatorio_completo("2024-01-01", "2024-12-31")
        
        print(f"Encontrados {len(relatorios)} relatórios")
        
        for i, relatorio in enumerate(relatorios[:3]):  # Mostra apenas os primeiros 3
            print(f"\n--- Relatório {i+1} ---")
            print(f"ID: {relatorio.id}")
            print(f"Código do Fundo: {relatorio.codigo_fundo}")
            print(f"Nome do Fundo: {relatorio.nome_fundo}")
            print(f"CNPJ: {relatorio.cnpj}")
            print(f"Data do Relatório: {relatorio.data_relatorio}")
            print(f"Patrimônio Líquido: {relatorio.patrimonio_liquido}")
            print(f"Ativo Total: {relatorio.ativo_total}")
            print(f"Passivo Total: {relatorio.passivo_total}")
            
            if relatorio.raw_data:
                print(f"Campos disponíveis nos dados brutos: {list(relatorio.raw_data.keys())}")
    
    except Exception as e:
        print(f"Erro ao buscar relatórios: {e}")
