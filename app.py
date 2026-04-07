import streamlit as st
import pdfplumber
import re
import pandas as pd
import numpy as np
from io import BytesIO
import base64
from datetime import datetime
import json
import plotly.express as px

st.set_page_config(
    page_title="Sistema Pro - Dimensionamento Visual",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTILO CSS PERSONALIZADO
# ==========================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .relatorio-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    .material-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BANCO DE DADOS DE MATERIAIS (EXPANSÍVEL)
# ==========================================
CATALOGO_MATERIAIS = {
    "adesivo_vinil": {
        "nome": "Adesivo Vinil",
        "unidade": "m²",
        "categoria": "Impressão Digital",
        "fator_perda": 1.10,
        "preco_unitario": 25.00
    },
    "lona_backlight": {
        "nome": "Lona Backlight",
        "unidade": "m²",
        "categoria": "Impressão Digital",
        "fator_perda": 1.15,
        "preco_unitario": 35.00
    },
    "lona_frontlit": {
        "nome": "Lona Frontlit",
        "unidade": "m²",
        "categoria": "Impressão Digital",
        "fator_perda": 1.10,
        "preco_unitario": 28.00
    },
    "acm_aluminio": {
        "nome": "ACM - Alumínio Composto",
        "unidade": "m²",
        "categoria": "Chapas Rígidas",
        "fator_perda": 1.05,
        "preco_unitario": 85.00
    },
    "pvc_expandido": {
        "nome": "PVC Expandido",
        "unidade": "m²",
        "categoria": "Chapas Rígidas",
        "fator_perda": 1.05,
        "preco_unitario": 65.00
    },
    "acrilico_transparente": {
        "nome": "Acrílico Transparente",
        "unidade": "m²",
        "categoria": "Chapas Rígidas",
        "fator_perda": 1.08,
        "preco_unitario": 120.00
    },
    "acrilico_leitoso": {
        "nome": "Acrílico Branco Leitoso",
        "unidade": "m²",
        "categoria": "Chapas Rígidas",
        "fator_perda": 1.08,
        "preco_unitario": 110.00
    },
    "poliestireno": {
        "nome": "Polietileno/Poliestireno",
        "unidade": "m²",
        "categoria": "Chapas Rígidas",
        "fator_perda": 1.05,
        "preco_unitario": 45.00
    },
    "chapa_galvanizada": {
        "nome": "Chapa Galvanizada",
        "unidade": "m²",
        "categoria": "Estrutura Metálica",
        "fator_perda": 1.12,
        "preco_unitario": 95.00
    },
    "led_modulo": {
        "nome": "Módulo de LED",
        "unidade": "W",
        "categoria": "Iluminação",
        "fator_perda": 1.0,
        "preco_unitario": 2.50
    },
    "fonte_led": {
        "nome": "Fonte LED",
        "unidade": "unidade",
        "categoria": "Iluminação",
        "fator_perda": 1.0,
        "preco_unitario": 85.00
    },
    "letra_inox": {
        "nome": "Letra em Aço Inox",
        "unidade": "cm",
        "categoria": "Letreiros",
        "fator_perda": 1.0,
        "preco_unitario": 4.50
    },
    "letra_acrylic": {
        "nome": "Letra em Acrílico",
        "unidade": "cm",
        "categoria": "Letreiros",
        "fator_perda": 1.0,
        "preco_unitario": 3.80
    },
    "pintura_automotiva": {
        "nome": "Pintura Automotiva",
        "unidade": "m²",
        "categoria": "Acabamento",
        "fator_perda": 1.20,
        "preco_unitario": 40.00
    },
    "fita_dupla_face": {
        "nome": "Fita Dupla Face",
        "unidade": "metro",
        "categoria": "Fixação",
        "fator_perda": 1.10,
        "preco_unitario": 3.50
    },
    "estrutura_metalica": {
        "nome": "Estrutura Metálica",
        "unidade": "kg",
        "categoria": "Estrutura Metálica",
        "fator_perda": 1.15,
        "preco_unitario": 18.00
    },
    "totem_completo": {
        "nome": "Totem Completo",
        "unidade": "unidade",
        "categoria": "Totens",
        "fator_perda": 1.0,
        "preco_unitario": 3500.00
    },
    "placa_sinalizacao": {
        "nome": "Placa de Sinalização",
        "unidade": "unidade",
        "categoria": "Sinalização",
        "fator_perda": 1.0,
        "preco_unitario": 120.00
    },
    "merchandising_grid": {
        "nome": "Merchandising Grid",
        "unidade": "unidade",
        "categoria": "PDV/Merchandising",
        "fator_perda": 1.0,
        "preco_unitario": 450.00
    },
    "pintura_coluna": {
        "nome": "Pintura de Coluna",
        "unidade": "m²",
        "categoria": "Acabamento",
        "fator_perda": 1.10,
        "preco_unitario": 35.00
    },
    "perfil_aluminio": {
        "nome": "Perfil de Alumínio",
        "unidade": "metro",
        "categoria": "Estrutura Metálica",
        "fator_perda": 1.05,
        "preco_unitario": 25.00
    },
    "parafuso": {
        "nome": "Parafusos e Fixadores",
        "unidade": "unidade",
        "categoria": "Fixação",
        "fator_perda": 1.0,
        "preco_unitario": 0.50
    },
    "silicone": {
        "nome": "Silicone para Vedação",
        "unidade": "metro",
        "categoria": "Fixação",
        "fator_perda": 1.10,
        "preco_unitario": 2.00
    }
}

# ==========================================
# FUNÇÕES AVANÇADAS DE EXTRAÇÃO
# ==========================================

def extrair_texto_pdf(arquivo):
    """Extrai texto do PDF com tratamento de encoding"""
    texto_completo = ""
    try:
        with pdfplumber.open(arquivo) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto = pagina.extract_text()
                if texto:
                    texto_completo += f"===== Página {i+1} =====\n{texto}\n"
                else:
                    texto = pagina.extract_text(layout=True)
                    if texto:
                        texto_completo += f"===== Página {i+1} =====\n{texto}\n"
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return ""
    return texto_completo

def extrair_medidas_ultra_avancado(texto):
    """Extrai medidas de QUALQUER formato encontrado na comunicação visual"""
    medidas = {}
    
    padroes = {
        "m2_direto": r"(\d+[.,]?\d*)\s*m[²2]",
        "largura_x_altura": r"(\d+[.,]?\d*)\s*[xX]\s*(\d+[.,]?\d*)\s*m",
        "cm_x_cm": r"(\d+)\s*cm\s*[xX]\s*(\d+)\s*cm",
        "altura_letra": r"(\d+)\s*cm\s*de\s*altura\s*de\s*letra",
        "diametro": r"di[âa]metro\s*de\s*(\d+[.,]?\d*)\s*m",
        "testeira": r"(\d+[.,]?\d*)\s*[Xx]\s*(\d+[.,]?\d*)\s*M",
        "altura_totem": r"[Hh]=(\d+[.,]?\d*)\s*M",
        "largura": r"largura\s+(\d+[.,]?\d*)\s*m",
        "altura": r"altura\s+(\d+[.,]?\d*)\s*m",
        "espessura": r"espessura\s+de\s+(\d+)\s*mm",
        "comprimento_linear": r"(\d+)\s*m\s+de\s+(\w+)",
        "m2_texto": r"(\d+[.,]?\d*)\s*metros?\s+quadrados",
        "volume": r"(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)",
        "potencia_led": r"(\d+[.,]?\d*)\s*W",
        "qtd_led": r"(\d+)\s*m[oó]dulos?\s+de\s+LED",
        "corrente_driver": r"(\d+)\s*A",
        "tensao": r"(\d+)\s*V"
    }
    
    for chave, padrao in padroes.items():
        matches = re.findall(padrao, texto, re.IGNORECASE)
        if matches:
            if chave in ["largura_x_altura", "testeira"]:
                for match in matches:
                    larg = float(match[0].replace(",", "."))
                    alt = float(match[1].replace(",", "."))
                    medidas["area_m2"] = larg * alt
            elif chave == "cm_x_cm":
                for match in matches:
                    larg_cm = float(match[0])
                    alt_cm = float(match[1])
                    medidas["area_m2"] = (larg_cm * alt_cm) / 10000
            elif chave == "comprimento_linear":
                for match in matches:
                    medidas["comprimento_m"] = float(match[0])
            elif chave in ["m2_direto", "m2_texto"]:
                for match in matches:
                    medidas["area_m2"] = float(match.replace(",", ".")) if isinstance(match, str) else float(match[0].replace(",", "."))
            else:
                for match in matches:
                    valor = float(match[0].replace(",", ".")) if isinstance(match, tuple) else float(match.replace(",", "."))
                    medidas[chave] = valor
    
    return medidas

def extrair_medidas_desenho_tecnico(texto):
    """Extrai medidas específicas de desenhos técnicos"""
    medidas = {}
    
    padroes = {
        "painel_dimensoes": r"Painel\s+(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)",
        "espessura_chapa": r"chapa\s+galvanizada\s*#?(\d+)",
        "espessura_acrilico": r"acr[íi]lico[s]?\s+de\s+(\d+)\s*mm",
        "temp_led": r"(\d+[.,]?\d*)\s*K\s*(?:kelvin)?",
        "potencia_fonte": r"Fonte\s+(\d+)\s*A",
        "modelo_led": r"M[oó]dulos?\s+([A-Za-z0-9\s]+?)(?:\s+de|\s+com|\s+\d+W|$)",
        "quantidade_led_detalhada": r"(\d+)\s*(?:unidades?|pe[çc]as?|m[oó]dulos?)\s+de\s+LED",
        "tipo_montagem": r"(face\s+unica|face\s+dupla|iluminado|backlight|frontlit)",
        "fixacao": r"fixa[çc][aã]o\s+com\s+(.+?)(?:\n|$)",
        "medida_estrutura": r"Estrutura\s+(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)"
    }
    
    for chave, padrao in padroes.items():
        matches = re.findall(padrao, texto, re.IGNORECASE)
        if matches:
            if chave == "painel_dimensoes":
                for match in matches:
                    larg = float(match[0].replace(",", "."))
                    alt = float(match[1].replace(",", "."))
                    medidas["largura_painel"] = larg
                    medidas["altura_painel"] = alt
                    medidas["area_painel"] = larg * alt
            elif chave == "espessura_chapa":
                medidas["bitola_chapa"] = int(matches[0])
                # #22 chapa = 0,76mm, #18 = 1,2mm, #16 = 1,5mm
                bitolas = {22: 0.76, 20: 0.95, 18: 1.2, 16: 1.5, 14: 1.9}
                medidas["espessura_chapa_mm"] = bitolas.get(int(matches[0]), 0.76)
            elif chave == "espessura_acrilico":
                medidas["espessura_acrilico_mm"] = int(matches[0])
            elif chave == "temp_led":
                medidas["temperatura_cor_led_k"] = float(matches[0])
            elif chave == "potencia_fonte":
                medidas["amperagem_fonte"] = float(matches[0])
            elif chave == "quantidade_led_detalhada":
                medidas["qtd_led"] = int(matches[0])
            elif chave == "tipo_montagem":
                medidas["tipo_painel"] = matches[0]
            elif chave == "medida_estrutura":
                for match in matches:
                    medidas["largura_estrutura"] = float(match[0].replace(",", "."))
                    medidas["altura_estrutura"] = float(match[1].replace(",", "."))
    
    return medidas

def extrair_cabecalho_completo(texto):
    """Extrai todas as informações do cabeçalho"""
    cabecalho = {
        "cliente": "",
        "razao_social": "",
        "local_instalacao": "",
        "contato": "",
        "endereco": "",
        "numero_op": "",
        "data": "",
        "observacoes": ""
    }
    
    match_op = re.search(r"OP[^\d]*(\d+)", texto, re.IGNORECASE)
    if match_op:
        cabecalho["numero_op"] = match_op.group(1)
    
    match_data = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", texto)
    if match_data:
        cabecalho["data"] = match_data.group(1)
    
    match_razao = re.search(r"Razão social:\s*(.+)", texto, re.IGNORECASE)
    if match_razao:
        cabecalho["razao_social"] = match_razao.group(1).strip()
        cabecalho["cliente"] = match_razao.group(1).strip()
    
    match_fantasia = re.search(r"Nome de Fantasia do Cliente:\s*(.+)", texto, re.IGNORECASE)
    if match_fantasia:
        cabecalho["cliente"] = match_fantasia.group(1).strip()
    
    match_local = re.search(r"Local da Instalação:\s*(.+)", texto, re.IGNORECASE)
    if match_local:
        cabecalho["local_instalacao"] = match_local.group(1).strip()
    
    match_contato = re.search(r"Contato[^:]*:\s*(.+)", texto, re.IGNORECASE)
    if match_contato:
        cabecalho["contato"] = match_contato.group(1).strip()
    
    match_end = re.search(r"Endereço Instalação[:\s]*(.+)", texto, re.IGNORECASE)
    if match_end:
        cabecalho["endereco"] = match_end.group(1).strip()
    
    match_obs = re.search(r"Observações?:\s*(.+)", texto, re.IGNORECASE)
    if match_obs:
        cabecalho["observacoes"] = match_obs.group(1).strip()
    
    return cabecalho

def extrair_itens_completos(texto):
    """Extrai todos os itens com suas descrições completas"""
    itens = []
    linhas = texto.split("\n")
    
    item_atual = None
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or len(linha) < 3:
            continue
        
        match = re.match(r"^([A-Za-z]\)?)\s*(\d+)\s+(.+)", linha, re.IGNORECASE)
        if match and "Item" not in linha and "DESCRIÇÃO" not in linha:
            if item_atual and item_atual.get("descricao"):
                itens.append(item_atual)
            
            codigo = match.group(1).replace(")", "")
            quantidade = int(match.group(2))
            descricao = match.group(3)
            
            item_atual = {
                "codigo": codigo,
                "quantidade": quantidade,
                "descricao": descricao,
                "descricao_completa": descricao
            }
        else:
            if item_atual:
                item_atual["descricao"] += " " + linha
                item_atual["descricao_completa"] += " " + linha
    
    if item_atual and item_atual.get("descricao"):
        itens.append(item_atual)
    
    for item in itens:
        item["medidas"] = extrair_medidas_ultra_avancado(item["descricao"])
        item["material_tipo"] = identificar_material_principal(item["descricao"])
    
    return itens

def identificar_material_principal(descricao):
    """Identifica automaticamente o tipo de material baseado na descrição"""
    desc = descricao.lower()
    
    mapeamento = {
        "adesivo": "adesivo_vinil",
        "lona backlight": "lona_backlight",
        "backlight": "lona_backlight",
        "lona": "lona_frontlit",
        "acm": "acm_aluminio",
        "alumínio composto": "acm_aluminio",
        "pvc expandido": "pvc_expandido",
        "acrílico transparente": "acrilico_transparente",
        "acrílico branco leitoso": "acrilico_leitoso",
        "poliestireno": "poliestireno",
        "chapa galvanizada": "chapa_galvanizada",
        "led": "led_modulo",
        "fonte": "fonte_led",
        "aço inox": "letra_inox",
        "letra em acrílico": "letra_acrylic",
        "pintura": "pintura_automotiva",
        "fita dupla face": "fita_dupla_face",
        "estrutura metálica": "estrutura_metalica",
        "totem": "totem_completo",
        "placa de sinalização": "placa_sinalizacao",
        "sinalização": "placa_sinalizacao",
        "merchandising": "merchandising_grid",
        "grid": "merchandising_grid",
        "pintura de coluna": "pintura_coluna",
        "perfil": "perfil_aluminio",
        "parafuso": "parafuso",
        "silicone": "silicone"
    }
    
    for palavra, material in mapeamento.items():
        if palavra in desc:
            return material
    
    return "outros"

def calcular_quantidade_material(item, material_info, medidas):
    """Calcula a quantidade total do material baseado nas regras de negócio"""
    qtd = item["quantidade"]
    area = medidas.get("area_m2", 0)
    comprimento = medidas.get("comprimento_m", 0)
    altura_letra = medidas.get("altura_letra", 0)
    
    tipo = item["material_tipo"]
    
    if tipo in ["adesivo_vinil", "lona_backlight", "lona_frontlit", "acm_aluminio", 
                "pvc_expandido", "acrilico_transparente", "acrilico_leitoso", 
                "poliestireno", "pintura_automotiva", "pintura_coluna", "chapa_galvanizada"]:
        if area > 0:
            total = area * qtd
        elif medidas.get("largura_m") and medidas.get("altura_m"):
            total = (medidas["largura_m"] * medidas["altura_m"]) * qtd
        else:
            total = 0
        return total * material_info["fator_perda"]
    
    elif tipo in ["letra_inox", "letra_acrylic"]:
        if altura_letra > 0:
            desc = item["descricao"].lower()
            palavras = re.findall(r'"([^"]+)"', desc)
            if palavras:
                num_letras = len(palavras[0].replace(" ", ""))
                total_cm = altura_letra * num_letras * qtd
                return total_cm
        return 0
    
    elif tipo == "led_modulo":
        qtd_leds = medidas.get("qtd_led", 0)
        potencia = medidas.get("potencia_led", 0)
        if qtd_leds > 0:
            return qtd_leds * qtd
        elif potencia > 0:
            return potencia * qtd
        return 0
    
    elif tipo == "fonte_led":
        return 1 * qtd
    
    elif tipo == "estrutura_metalica":
        if area > 0:
            kg = area * 12 * qtd
            return kg * material_info["fator_perda"]
        return 0
    
    elif tipo == "fita_dupla_face":
        if medidas.get("largura_m") and medidas.get("altura_m"):
            perimetro = 2 * (medidas["largura_m"] + medidas["altura_m"])
            return perimetro * qtd
        return comprimento * qtd
    
    elif tipo == "perfil_aluminio":
        if medidas.get("largura_m") and medidas.get("altura_m"):
            perimetro = 2 * (medidas["largura_m"] + medidas["altura_m"])
            return perimetro * qtd * 1.1
        return comprimento * qtd
    
    elif tipo in ["totem_completo", "placa_sinalizacao", "merchandising_grid", "parafuso", "silicone"]:
        return qtd
    
    return 0

def calcular_material_desenho_tecnico(medidas, qtd=1):
    """Calcula materiais específicos para desenhos técnicos"""
    resultados = {}
    
    if "area_painel" in medidas and medidas["area_painel"] > 0:
        area = medidas["area_painel"]
        
        resultados["acm_aluminio"] = {
            "quantidade": area * qtd,
            "unidade": "m²",
            "material": "ACM - Alumínio Composto 2mm"
        }
        
        if "espessura_acrilico_mm" in medidas:
            resultados["acrilico_leitoso"] = {
                "quantidade": area * qtd,
                "unidade": "m²",
                "material": f"Acrílico Branco Leitoso {medidas['espessura_acrilico_mm']}mm"
            }
        
        if "bitola_chapa" in medidas:
            resultados["chapa_galvanizada"] = {
                "quantidade": area * qtd * 1.05,
                "unidade": "m²",
                "material": f"Chapa Galvanizada #{medidas['bitola_chapa']}"
            }
        
        resultados["estrutura_metalica"] = {
            "quantidade": area * 12 * qtd,
            "unidade": "kg",
            "material": "Estrutura Metálica (suporte)"
        }
        
        perimetro = 2 * (medidas.get("largura_painel", 1) + medidas.get("altura_painel", 1))
        resultados["perfil_aluminio"] = {
            "quantidade": perimetro * qtd,
            "unidade": "metro",
            "material": "Perfil de Alumínio para Moldura"
        }
        
        resultados["parafuso"] = {
            "quantidade": int(area * 8) * qtd,
            "unidade": "unidade",
            "material": "Parafusos autoatarrachantes"
        }
        
        resultados["silicone"] = {
            "quantidade": perimetro * qtd,
            "unidade": "metro",
            "material": "Silicone para vedação"
        }
    
    if "qtd_led" in medidas and medidas["qtd_led"] > 0:
        resultados["led_modulo"] = {
            "quantidade": medidas["qtd_led"] * qtd,
            "unidade": "unidade",
            "material": "Módulo LED"
        }
        
        if "potencia_led" in medidas:
            resultados["potencia_led_total"] = {
                "quantidade": medidas["qtd_led"] * medidas["potencia_led"] * qtd,
                "unidade": "W",
                "material": "Potência LED Total"
            }
    
    if "amperagem_fonte" in medidas:
        resultados["fonte_led"] = {
            "quantidade": qtd,
            "unidade": "unidade",
            "material": f"Fonte LED {medidas['amperagem_fonte']}A"
        }
    
    return resultados

# ==========================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ==========================================

def processar_pdf_completo(arquivo):
    """Processa o PDF e retorna todos os dados estruturados"""
    texto = extrair_texto_pdf(arquivo)
    if not texto:
        return None, None
    
    cabecalho = extrair_cabecalho_completo(texto)
    itens = extrair_itens_completos(texto)
    medidas_desenho = extrair_medidas_desenho_tecnico(texto)
    
    resultados = []
    
    # Processa itens da tabela
    for item in itens:
        material_id = item["material_tipo"]
        material_info = CATALOGO_MATERIAIS.get(material_id, {
            "nome": "Outros Materiais",
            "unidade": "unidade",
            "categoria": "Diversos",
            "fator_perda": 1.0,
            "preco_unitario": 0
        })
        
        quantidade_calculada = calcular_quantidade_material(item, material_info, item["medidas"])
        
        resultado = {
            "codigo": item["codigo"],
            "quantidade_op": item["quantidade"],
            "descricao": item["descricao"][:80],
            "material": material_info["nome"],
            "categoria": material_info["categoria"],
            "unidade": material_info["unidade"],
            "quantidade_calculada": round(quantidade_calculada, 2),
            "preco_unitario": material_info["preco_unitario"],
            "total_material": round(quantidade_calculada * material_info["preco_unitario"], 2),
            "detalhes": f"Área: {item['medidas'].get('area_m2', 0):.2f}m²" if item['medidas'].get('area_m2') else "Sem medidas específicas"
        }
        resultados.append(resultado)
    
    # Se for desenho técnico (sem itens na tabela mas com medidas de painel)
    if len(resultados) == 0 and medidas_desenho.get("area_painel", 0) > 0:
        st.info("📐 Desenho técnico detectado! Calculando materiais automaticamente...")
        
        materiais_desenho = calcular_material_desenho_tecnico(medidas_desenho, 1)
        
        for mat_key, mat_data in materiais_desenho.items():
            material_info = CATALOGO_MATERIAIS.get(mat_key, {
                "nome": mat_data["material"],
                "unidade": mat_data["unidade"],
                "categoria": "Desenho Técnico",
                "fator_perda": 1.0,
                "preco_unitario": 0
            })
            
            resultado = {
                "codigo": "TEC",
                "quantidade_op": 1,
                "descricao": mat_data["material"][:80],
                "material": mat_data["material"],
                "categoria": material_info["categoria"],
                "unidade": mat_data["unidade"],
                "quantidade_calculada": round(mat_data["quantidade"], 2),
                "preco_unitario": material_info["preco_unitario"],
                "total_material": round(mat_data["quantidade"] * material_info["preco_unitario"], 2),
                "detalhes": f"Painel {medidas_desenho.get('largura_painel', 0)} x {medidas_desenho.get('altura_painel', 0)}m"
            }
            resultados.append(resultado)
    
    return cabecalho, resultados

# ==========================================
# GERADOR DE RELATÓRIO HTML PROFISSIONAL
# ==========================================

def gerar_relatorio_html(cabecalho, resultados):
    """Gera relatório HTML completo com design profissional"""
    
    total_geral = sum(r["total_material"] for r in resultados)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Dimensionamento - OP {cabecalho.get('numero_op', '')}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f0f2f5;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                padding: 30px;
                background: #f8f9fa;
            }}
            .info-card {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .info-card h3 {{
                color: #667eea;
                margin-bottom: 10px;
                font-size: 14px;
                text-transform: uppercase;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #e0e0e0;
            }}
            tr:hover {{ background: #f5f5f5; }}
            .total {{
                margin: 20px;
                padding: 20px;
                background: #e8f4f8;
                border-radius: 8px;
                text-align: right;
            }}
            .footer {{
                background: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 12px;
            }}
            @media print {{
                body {{ background: white; padding: 0; }}
                .btn-print {{ display: none; }}
            }}
            .btn-print {{
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                margin: 20px;
                float: right;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📐 RELATÓRIO DE DIMENSIONAMENTO</h1>
                <p>Sistema Profissional para Comunicação Visual</p>
                <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <div class="info-grid">
                <div class="info-card"><h3>🏢 CLIENTE</h3><p>{cabecalho.get('cliente', 'NÃO INFORMADO')}</p></div>
                <div class="info-card"><h3>📍 LOCAL</h3><p>{cabecalho.get('local_instalacao', 'NÃO INFORMADO')}</p></div>
                <div class="info-card"><h3>📞 CONTATO</h3><p>{cabecalho.get('contato', 'NÃO INFORMADO')}</p></div>
                <div class="info-card"><h3>🔢 OP Nº</h3><p>{cabecalho.get('numero_op', 'NÃO INFORMADO')}</p></div>
            </div>
            
            <div style="padding: 0 30px;">
                <h2>📦 MATERIAIS DIMENSIONADOS</h2>
                <table>
                    <thead><tr><th>Código</th><th>Qtd OP</th><th>Descrição</th><th>Material</th><th>Unidade</th><th>Quantidade</th><th>Total (R$)</th></tr></thead>
                    <tbody>
    """
    
    for r in resultados:
        html += f"""
            <tr>
                <td>{r['codigo']}</td>
                <td>{r['quantidade_op']}</td>
                <td>{r['descricao']}</td>
                <td>{r['material']}</td>
                <td>{r['unidade']}</td>
                <td><strong>{r['quantidade_calculada']}</strong></td>
                <td><strong>R$ {r['total_material']:.2f}</strong></td>
            </tr>
        """
    
    html += f"""
                    </tbody>
                </table>
                <div class="total"><h2>💰 TOTAL GERAL: R$ {total_geral:.2f}</h2></div>
            </div>
            <div class="footer">
                <p>Relatório gerado automaticamente pelo Sistema de Dimensionamento Profissional</p>
            </div>
        </div>
        <button class="btn-print" onclick="window.print()">🖨️ IMPRIMIR RELATÓRIO</button>
    </body>
    </html>
    """
    return html

# ==========================================
# INTERFACE PRINCIPAL STREAMLIT
# ==========================================

def main():
    with st.sidebar:
        st.markdown("## 🎯 Sistema Profissional")
        st.markdown("---")
        st.markdown("### 📋 Funcionalidades:")
        st.markdown("""
        - ✅ Leitura de PDFs de OP
        - ✅ Leitura de desenhos técnicos
        - ✅ Extração de medidas (m², cm, etc.)
        - ✅ Cálculo de materiais
        - ✅ Relatório profissional
        - ✅ Exportação CSV/HTML
        """)
        st.markdown("---")
        st.markdown("### 🏆 Materiais Suportados:")
        st.markdown("""
        - Adesivos e lonas (m²)
        - ACM, PVC, Acrílico (m²)
        - Letras em inox/acrílico (cm)
        - Totens e estruturas
        - Sinalização completa
        - Iluminação LED
        - Chapas galvanizadas
        - Perfis de alumínio
        - Fixadores e silicones
        """)
    
    st.markdown("""
    <div class="main-header">
        <h1>📐 SISTEMA PROFISSIONAL DE DIMENSIONAMENTO</h1>
        <p>Comunicação Visual - Cálculo Automático de Materiais</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📄 Envie o PDF (OP ou Desenho Técnico)", type=["pdf"])
    
    if uploaded_file is not None:
        with st.spinner("🔄 Processando PDF..."):
            cabecalho, resultados = processar_pdf_completo(uploaded_file)
            
            if resultados and len(resultados) > 0:
                st.success(f"✅ Processado! {len(resultados)} materiais calculados.")
                
                tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Materiais", "🖨️ Relatório"])
                
                with tab1:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Itens", len(resultados))
                    with col2:
                        total_geral = sum(r["total_material"] for r in resultados)
                        st.metric("Valor Total", f"R$ {total_geral:,.2f}")
                    with col3:
                        qtd_total = sum(r["quantidade_op"] for r in resultados)
                        st.metric("Quantidade Total", qtd_total)
                    
                    st.markdown("---")
                    st.subheader("🏢 Informações do Projeto")
                    st.write(f"**Cliente:** {cabecalho.get('cliente', 'N/A')}")
                    st.write(f"**Local:** {cabecalho.get('local_instalacao', 'N/A')}")
                    st.write(f"**OP Número:** {cabecalho.get('numero_op', 'N/A')}")
                
                with tab2:
                    df = pd.DataFrame(resultados)
                    st.dataframe(df, use_column_width=True, height=400)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Baixar CSV", csv, f"dimensionamento_{cabecalho.get('numero_op', 'op')}.csv", "text/csv")
                    
                    if len(df) > 0:
                        df_cat = df.groupby("categoria")["total_material"].sum().reset_index()
                        fig = px.pie(df_cat, values="total_material", names="categoria", title="Distribuição por Categoria")
                        st.plotly_chart(fig, use_column_width=True)
                
                with tab3:
                    html_relatorio = gerar_relatorio_html(cabecalho, resultados)
                    st.components.v1.html(html_relatorio, height=500, scrolling=True)
                    
                    b64 = base64.b64encode(html_relatorio.encode()).decode()
                    st.markdown(f'<a href="data:text/html;base64,{b64}" download="relatorio_{cabecalho.get("numero_op", "op")}.html" style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📥 Baixar Relatório HTML</a>', unsafe_allow_html=True)
            else:
                st.error("❌ Não foi possível extrair dados do PDF. Verifique o formato.")
    else:
        st.info("👈 **Envie um arquivo PDF** (OP ou desenho técnico) para começar")
        
        with st.expander("📖 Como funciona?"):
            st.markdown("""
            ### 🔍 O sistema reconhece:
            
            **Ordens de Produção:**
            - Itens com código e quantidade
            - Medidas como `61,93m²`, `2,22 x 1,70m`, `15cm de altura`
            
            **Desenhos Técnicos:**
            - Dimensões de painel (`2,22 x 1,70`)
            - Componentes (`180 módulos LED`, `Fonte 12A`)
            - Materiais (`chapa galvanizada #22`, `acrílico 4mm`)
            
            ### 📊 Resultados:
            - Lista completa de materiais com quantidades
            - Cálculo de perdas (5-15%)
            - Estimativa de custos
            - Relatório para impressão
            """)

if __name__ == "__main__":
    main()
