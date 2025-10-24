"""
Agente Service - Utilitários e Ferramentas de Apoio
==================================================

Este agente não interage diretamente com clientes, mas fornece 
ferramentas e validações para apoiar outros agentes.

Funcionalidades:
- Validação de dados de clientes
- Formatação de endereços
- Validação de telefones/CEPs
- Cálculo de prazos de entrega
- Formatação de respostas
- Utilidades gerais do sistema
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("3afrios.service_utils")

class ServiceUtils:
    """Classe com utilitários para apoiar outros agentes"""
    
    @staticmethod
    def validar_telefone(telefone: str) -> Dict[str, Any]:
        """
        Valida e normaliza número de telefone brasileiro
        """
        if not telefone:
            return {"valido": False, "erro": "Telefone vazio"}
        
        # Remove caracteres não numéricos
        numeros = re.sub(r'\D', '', str(telefone))
        
        # Validações básicas
        if len(numeros) < 10:
            return {"valido": False, "erro": "Telefone muito curto"}
        elif len(numeros) > 11:
            return {"valido": False, "erro": "Telefone muito longo"}
        
        # Formatar baseado no tamanho
        if len(numeros) == 10:  # Fixo
            formatado = f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
            tipo = "fixo"
        else:  # Celular
            formatado = f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
            tipo = "celular"
        
        return {
            "valido": True,
            "normalizado": numeros,
            "formatado": formatado,
            "tipo": tipo,
            "ddd": numeros[:2]
        }
    
    @staticmethod
    def validar_cep(cep: str) -> Dict[str, Any]:
        """
        Valida formato de CEP brasileiro
        """
        if not cep:
            return {"valido": False, "erro": "CEP vazio"}
        
        # Remove caracteres não numéricos
        numeros = re.sub(r'\D', '', str(cep))
        
        if len(numeros) != 8:
            return {"valido": False, "erro": "CEP deve ter 8 dígitos"}
        
        # Formato padrão: 12345-678
        formatado = f"{numeros[:5]}-{numeros[5:]}"
        
        return {
            "valido": True,
            "normalizado": numeros,
            "formatado": formatado
        }
    
    @staticmethod
    def calcular_prazo_entrega(cep_destino: str = None, peso_kg: float = 0) -> Dict[str, Any]:
        """
        Calcula prazo estimado de entrega baseado no CEP
        """
        # Lógica simplificada - pode ser expandida com API dos Correios
        prazo_base = 2  # dias
        
        if cep_destino:
            cep_info = ServiceUtils.validar_cep(cep_destino)
            if cep_info["valido"]:
                # Lógica baseada na região (primeiros dígitos do CEP)
                regiao = cep_info["normalizado"][:2]
                
                # Regiões próximas (exemplo: SE, Sul)
                if regiao in ["01", "02", "03", "04", "05", "08", "09"]:  # SP
                    prazo_base = 1
                elif regiao in ["20", "21", "22", "23", "24", "28"]:  # RJ
                    prazo_base = 2
                elif regiao in ["30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:  # MG
                    prazo_base = 2
                else:  # Outras regiões
                    prazo_base = 3
        
        # Ajuste por peso (produtos mais pesados podem demorar mais)
        if peso_kg > 10:
            prazo_base += 1
        
        # Considera fins de semana
        hoje = datetime.now()
        data_entrega = hoje + timedelta(days=prazo_base)
        
        # Se cair no fim de semana, empurra para segunda
        while data_entrega.weekday() >= 5:  # 5=sábado, 6=domingo
            data_entrega += timedelta(days=1)
        
        return {
            "prazo_dias": prazo_base,
            "data_estimada": data_entrega.strftime("%d/%m/%Y"),
            "data_limite": (data_entrega + timedelta(days=1)).strftime("%d/%m/%Y"),
            "info": f"Entrega em {prazo_base} dias úteis"
        }
    
    @staticmethod
    def formatar_endereco(endereco_dict: Dict[str, str]) -> str:
        """
        Formata endereço de forma padronizada
        """
        try:
            logradouro = endereco_dict.get("logradouro", "")
            numero = endereco_dict.get("numero", "S/N")
            complemento = endereco_dict.get("complemento", "")
            bairro = endereco_dict.get("bairro", "")
            cidade = endereco_dict.get("cidade", "")
            uf = endereco_dict.get("uf", "")
            cep = endereco_dict.get("cep", "")
            
            # Monta endereço
            endereco_completo = f"{logradouro}, {numero}"
            if complemento:
                endereco_completo += f", {complemento}"
            endereco_completo += f"\n{bairro} - {cidade}/{uf}"
            if cep:
                cep_formatado = ServiceUtils.validar_cep(cep)
                if cep_formatado["valido"]:
                    endereco_completo += f"\nCEP: {cep_formatado['formatado']}"
            
            return endereco_completo
            
        except Exception as e:
            logger.error(f"Erro ao formatar endereço: {e}")
            return "Endereço não disponível"
    
    @staticmethod
    def validar_dados_cliente(dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida conjunto de dados do cliente
        """
        validacoes = {
            "telefone": None,
            "cep": None,
            "endereco_completo": None,
            "valido_geral": True,
            "erros": []
        }
        
        # Valida telefone
        if "telefone" in dados:
            tel_result = ServiceUtils.validar_telefone(dados["telefone"])
            validacoes["telefone"] = tel_result
            if not tel_result["valido"]:
                validacoes["valido_geral"] = False
                validacoes["erros"].append(f"Telefone: {tel_result['erro']}")
        
        # Valida CEP
        if "cep" in dados:
            cep_result = ServiceUtils.validar_cep(dados["cep"])
            validacoes["cep"] = cep_result
            if not cep_result["valido"]:
                validacoes["valido_geral"] = False
                validacoes["erros"].append(f"CEP: {cep_result['erro']}")
        
        # Formata endereço se disponível
        if all(k in dados for k in ["logradouro", "cidade", "uf"]):
            validacoes["endereco_completo"] = ServiceUtils.formatar_endereco(dados)
        
        return validacoes
    
    @staticmethod
    def formatar_valor_monetario(valor: float) -> str:
        """
        Formata valor em reais
        """
        try:
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"
    
    @staticmethod
    def extrair_quantidades_texto(texto: str) -> List[Dict[str, Any]]:
        """
        Extrai quantidades mencionadas no texto (kg, gramas, unidades)
        """
        quantidades = []
        
        # Padrões para detectar quantidades
        padroes = [
            r'(\d+(?:,\d+)?)\s*(?:kg|quilo|quilos)',
            r'(\d+)\s*(?:g|grama|gramas)',
            r'(\d+)\s*(?:unidade|unidades|peça|peças)',
            r'(\d+)\s*(?:litro|litros|l)',
            r'meio\s+(?:kg|quilo)',
            r'um\s+(?:kg|quilo)',
            r'dois\s+(?:kg|quilos)',
            r'três\s+(?:kg|quilos)'
        ]
        
        texto_lower = texto.lower()
        
        for padrao in padroes:
            matches = re.finditer(padrao, texto_lower)
            for match in matches:
                if 'kg' in padrao or 'quilo' in padrao:
                    if 'meio' in match.group(0):
                        quantidade = 0.5
                    elif 'um' in match.group(0):
                        quantidade = 1.0
                    elif 'dois' in match.group(0):
                        quantidade = 2.0
                    elif 'três' in match.group(0):
                        quantidade = 3.0
                    else:
                        quantidade = float(match.group(1).replace(',', '.'))
                    
                    quantidades.append({
                        "valor": quantidade,
                        "unidade": "kg",
                        "texto_original": match.group(0)
                    })
                
                elif 'g' in padrao or 'grama' in padrao:
                    quantidade = float(match.group(1)) / 1000  # Converter para kg
                    quantidades.append({
                        "valor": quantidade,
                        "unidade": "kg",
                        "texto_original": match.group(0)
                    })
                
                elif 'unidade' in padrao or 'peça' in padrao:
                    quantidade = int(match.group(1))
                    quantidades.append({
                        "valor": quantidade,
                        "unidade": "unidade",
                        "texto_original": match.group(0)
                    })
        
        return quantidades


# Mantém compatibilidade com versão anterior para não quebrar importações
def respond(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Interface de compatibilidade - agora retorna ferramentas de apoio
    """
    # Se algum agente ainda chamar diretamente, redireciona para Atendimento
    return {
        'resposta': 'Este agente agora funciona como utilitário interno. Use o agente de Atendimento para interações com clientes.',
        'acao_especial': '[REDIRECT:ATENDIMENTO]',
        'tools_available': [
            'validar_telefone',
            'validar_cep', 
            'calcular_prazo_entrega',
            'formatar_endereco',
            'validar_dados_cliente',
            'formatar_valor_monetario',
            'extrair_quantidades_texto'
        ]
    }


# Instância global para uso pelos outros agentes
service_utils = ServiceUtils()

# Função de conveniência para outros agentes importarem
def get_service_utils() -> ServiceUtils:
    """Retorna instância dos utilitários do Service"""
    return service_utils