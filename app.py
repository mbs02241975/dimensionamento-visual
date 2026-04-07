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
                    # Tenta extrair com layout preservado
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
    
    # Padrões de medida
    padroes = {
        # m² direto (61,93m², 15.5m²)
        "m2_direto": r"(\d+[.,]?\d*)\s*m[²2]",
        
        # Largura x Altura (2,22 x 1,70m)
        "largura_x_altura": r"(\d+[.,]?\d*)\s*[xX]\s*(\d+[.,]?\d*)\s*m",
        
        # Medidas em cm (60cm x 40cm)
        "cm_x_cm": r"(\d+)\s*cm\s*[xX]\s*(\d+)\s*cm",
        
        # Altura de letra (15cm de altura)
        "altura_letra": r"(\d+)\s*cm\s*de\s*altura\s*de\s*letra",
        
        # Diâmetro (diâmetro de 0,70m)
        "diametro": r"di[âa]metro\s*de\s*(\d+[.,]?\d*)\s*m",
        
        # Testeira/lona (15,50 X 1,00M)
        "testeira": r"(\d+[.,]?\d*)\s*[Xx]\s*(\d+[.,]?\d*)\s*M",
        
        # Altura de totem (H=5 M, H=5m)
        "altura_totem": r"[Hh]=(\d+[.,]?\d*)\s*M",
        
        # Largura fixa (largura 1,30m)
        "largura": r"largura\s+(\d+[.,]?\d*)\s*m",
        
        # Altura fixa (altura 0,60m)
        "altura": r"altura\s+(\d+[.,]?\d*)\s*m",
        
        # Espessura (espessura de 40mm)
        "espessura": r"espessura\s+de\s+(\d+)\s*mm",
        
        # Comprimento linear (82m de testeira)
        "comprimento_linear": r"(\d+)\s*m\s+de\s+(\w+)",
        
        # Metros quadrados em texto (61,93 metros quadrados)
        "m2_texto": r"(\d+[.,]?\d*)\s*metros?\s+quadrados",
        
        # Volume (caso tenha profundidade)
        "volume": r"(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)",
        
        # Potência LED (0,72 W)
        "potencia_led": r"(\d+[.,]?\d*)\s*W",
        
        # Quantidade de módulos LED (180 módulos)
        "qtd_led": r"(\d+)\s*m[oó]dulos?\s+de\s+LED",
        
        # Área de painel (Painel 2,22 x 1,70)
        "painel": r"Painel\s+(\d+[.,]?\d*)\s*x\s*(\d+[.,]?\d*)",
        
        # Corrente do driver (12 A)
        "corrente_driver": r"(\d+)\s*A",
        
        # Tensão (220 V)
        "tensao": r"(\d+)\s*V"
    }
    
    for chave, padrao in padroes.items():
        matches = re.findall(padrao, texto, re.IGNORECASE)
        if matches:
            if chave == "largura_x_altura" or chave == "painel" or chave == "testeira":
                for match in matches:
                    larg = float(match[0].replace(",", "."))
                    alt = float(match[1].replace(",", "."))
                    medidas[f"{chave}_largura"] = larg
                    medidas[f"{chave}_altura"] = alt
                    medidas["area_m2"] = larg * alt
            elif chave == "cm_x_cm":
                for match in matches:
                    larg_cm = float(match[0])
                    alt_cm = float(match[1])
                    medidas["largura_cm"] = larg_cm
                    medidas["altura_cm"] = alt_cm
                    medidas["area_m2"] = (larg_cm * alt_cm) / 10000
            elif chave == "volume":
                for match in matches:
                    comp = float(match[0].replace(",", "."))
                    larg = float(match[1].replace(",", "."))
                    alt = float(match[2].replace(",", "."))
                    medidas["volume_m3"] = comp * larg * alt
            elif chave == "comprimento_linear":
                for match in matches:
                    medidas["comprimento_m"] = float(match[0])
                    medidas["tipo_linear"] = match[1]
            elif chave in ["m2_direto", "m2_texto"]:
                for match in matches:
                    medidas["area_m2"] = float(match.replace(",", ".")) if isinstance(match, str) else float(match[0].replace(",", "."))
            else:
                for match in matches:
                    valor = float(match[0].replace(",", ".")) if isinstance(match, tuple) else float(match.replace(",", "."))
                    medidas[chave] = valor
    
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
    
    # Número da OP
    match_op = re.search(r"OP[^\d]*(\d+)", texto, re.IGNORECASE)
    if match_op:
        cabecalho["numero_op"] = match_op.group(1)
    
    # Data
    match_data = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", texto)
    if match_data:
        cabecalho["data"] = match_data.group(1)
    
    # Razão social
    match_razao = re.search(r"Razão social:\s*(.+)", texto, re.IGNORECASE)
    if match_razao:
        cabecalho["razao_social"] = match_razao.group(1).strip()
        cabecalho["cliente"] = match_razao.group(1).strip()
    
    # Nome fantasia
    match_fantasia = re.search(r"Nome de Fantasia do Cliente:\s*(.+)", texto, re.IGNORECASE)
    if match_fantasia:
        cabecalho["cliente"] = match_fantasia.group(1).strip()
    
    # Local da instalação
    match_local = re.search(r"Local da Instalação:\s*(.+)", texto, re.IGNORECASE)
    if match_local:
        cabecalho["local_instalacao"] = match_local.group(1).strip()
    
    # Contato
    match_contato = re.search(r"Contato[^:]*:\s*(.+)", texto, re.IGNORECASE)
    if match_contato:
        cabecalho["contato"] = match_contato.group(1).strip()
    
    # Endereço
    match_end = re.search(r"Endereço Instalação[:\s]*(.+)", texto, re.IGNORECASE)
    if match_end:
        cabecalho["endereco"] = match_end.group(1).strip()
    
    # Observações
    match_obs = re.search(r"Observações?:\s*(.+)", texto, re.IGNORECASE)
    if match_obs:
        cabecalho["observacoes"] = match_obs.group(1).strip()
    
    return cabecalho

def extrair_itens_completos(texto):
    """Extrai todos os itens com suas descrições completas"""
    itens = []
    linhas = texto.split("\n")
    
    # Padrões de início de item
    padroes_item = [
        r"^([A-Za-z]\)?)\s*(\d+)\s+(.+)",  # A) 10 Descrição
        r"^Item\s+Quantidade\s+Engenho",  # Cabeçalho de tabela
        r"^([A-Z])\s+(\d+)\s+",  # A 10
    ]
    
    item_atual = None
    
    for i, linha in enumerate(linhas):
        linha = linha.strip()
        if not linha or len(linha) < 3:
            continue
        
        # Detecta início de item
        for padrao in padroes_item:
            match = re.match(padrao, linha, re.IGNORECASE)
            if match and "Item" not in linha:
                # Salva item anterior
                if item_atual and item_atual.get("descricao"):
                    itens.append(item_atual)
                
                # Cria novo item
                codigo = match.group(1).replace(")", "") if len(match.groups()) >= 1 else chr(65 + len(itens))
                quantidade = int(match.group(2)) if len(match.groups()) >= 2 else 1
                descricao = match.group(3) if len(match.groups()) >= 3 else ""
                
                item_atual = {
                    "codigo": codigo,
                    "quantidade": quantidade,
                    "descricao": descricao,
                    "descricao_completa": descricao
                }
                break
        else:
            # Continua descrição do item atual
            if item_atual:
                item_atual["descricao"] += " " + linha
                item_atual["descricao_completa"] += " " + linha
    
    # Adiciona último item
    if item_atual and item_atual.get("descricao"):
        itens.append(item_atual)
    
    # Extrai medidas para cada item
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
        "estrutura metalica": "estrutura_metalica",
        "totem": "totem_completo",
        "placa de sinalização": "placa_sinalizacao",
        "sinalização": "placa_sinalizacao",
        "merchandising": "merchandising_grid",
        "grid": "merchandising_grid",
        "pintura de coluna": "pintura_coluna"
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
    
    # Regras específicas por tipo de material
    if tipo in ["adesivo_vinil", "lona_backlight", "lona_frontlit", "acm_aluminio", 
                "pvc_expandido", "acrilico_transparente", "acrilico_leitoso", 
                "poliestireno", "pintura_automotiva", "pintura_coluna"]:
        # Materiais por área
        if area > 0:
            total = area * qtd
        elif medidas.get("largura_m") and medidas.get("altura_m"):
            total = (medidas["largura_m"] * medidas["altura_m"]) * qtd
        else:
            total = 0
        return total * material_info["fator_perda"]
    
    elif tipo in ["letra_inox", "letra_acrylic"]:
        # Letras - calcula por centímetro linear
        if altura_letra > 0:
            # Estima número de letras pela descrição
            desc = item["descricao"].lower()
            palavras = re.findall(r'"([^"]+)"', desc)
            if palavras:
                num_letras = len(palavras[0].replace(" ", ""))
                total_cm = altura_letra * num_letras * qtd
                return total_cm
        return 0
    
    elif tipo == "led_modulo":
        # Módulos LED - por watt ou por unidade
        potencia = medidas.get("potencia_led", 0)
        qtd_leds = medidas.get("qtd_led", 0)
        if qtd_leds > 0:
            return qtd_leds * qtd
        elif potencia > 0:
            return potencia * qtd
        return 0
    
    elif tipo == "fonte_led":
        # Fonte LED - por ampere
        corrente = medidas.get("corrente_driver", 0)
        if corrente > 0:
            return 1 * qtd  # Uma fonte por conjunto
        return 0
    
    elif tipo == "estrutura_metalica":
        # Estrutura metálica - estimativa por área
        if area > 0:
            # Estimativa: 8kg por m² de estrutura
            kg = area * 8 * qtd
            return kg * material_info["fator_perda"]
        return 0
    
    elif tipo == "fita_dupla_face":
        # Fita dupla face - estimativa por perímetro
        if medidas.get("largura_m") and medidas.get("altura_m"):
            perimetro = 2 * (medidas["largura_m"] + medidas["altura_m"])
            return perimetro * qtd
        return comprimento * qtd
    
    elif tipo == "totem_completo":
        return qtd
    
    elif tipo == "placa_sinalizacao":
        return qtd
    
    elif tipo == "merchandising_grid":
        return qtd
    
    elif tipo == "chapa_galvanizada":
        if area > 0:
            return area * qtd * material_info["fator_perda"]
        return 0
    
    return 0

# ==========================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ==========================================

def processar_pdf_completo(arquivo):
    """Processa o PDF e retorna todos os dados estruturados"""
    texto = extrair_texto_pdf(arquivo)
    if not texto:
        return None, None, None
    
    cabecalho = extrair_cabecalho_completo(texto)
    itens = extrair_itens_completos(texto)
    
    # Processa cada item
    resultados = []
    for item in itens:
        material_id = item["material_tipo"]
        material_info = CATALOGO_MATERIAIS.get(material_id, {
            "nome": "Outros Materiais",
            "unidade": "unidade",
            "fator_perda": 1.0,
            "preco_unitario": 0
        })
        
        quantidade_calculada = calcular_quantidade_material(item, material_info, item["medidas"])
        
        resultado = {
            "codigo": item["codigo"],
            "quantidade_op": item["quantidade"],
            "descricao": item["descricao"][:100],
            "material": material_info["nome"],
            "categoria": material_info["categoria"],
            "unidade": material_info["unidade"],
            "quantidade_calculada": round(quantidade_calculada, 2),
            "preco_unitario": material_info["preco_unitario"],
            "total_material": round(quantidade_calculada * material_info["preco_unitario"], 2),
            "medidas_extraidas": json.dumps(item["medidas"], ensure_ascii=False),
            "detalhes": f"Área: {item['medidas'].get('area_m2', 0):.2f}m²" if item['medidas'].get('area_m2') else "Sem medidas específicas"
        }
        resultados.append(resultado)
    
    return cabecalho, resultados, texto

# ==========================================
# GERADOR DE RELATÓRIO HTML PROFISSIONAL
# ==========================================

def gerar_relatorio_html(cabecalho, resultados, nome_arquivo=""):
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
            .header h1 {{
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .header p {{
                opacity: 0.9;
            }}
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
                letter-spacing: 1px;
            }}
            .info-card p {{
                color: #333;
                font-size: 16px;
                font-weight: 500;
            }}
            .content {{
                padding: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #e0e0e0;
            }}
            tr:hover {{
                background: #f5f5f5;
            }}
            .total {{
                margin-top: 30px;
                padding: 20px;
                background: #e8f4f8;
                border-radius: 8px;
                text-align: right;
            }}
            .total h2 {{
                color: #2c3e50;
            }}
            .footer {{
                background: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 12px;
            }}
            @media print {{
                body {{
                    background: white;
                    padding: 0;
                }}
                .btn-print {{
                    display: none;
                }}
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
            .btn-print:hover {{
                background: #5a67d8;
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
                <div class="info-card">
                    <h3>🏢 CLIENTE</h3>
                    <p>{cabecalho.get('cliente', 'NÃO INFORMADO')}</p>
                </div>
                <div class="info-card">
                    <h3>📍 LOCAL DA INSTALAÇÃO</h3>
                    <p>{cabecalho.get('local_instalacao', 'NÃO INFORMADO')}</p>
                </div>
                <div class="info-card">
                    <h3>📞 CONTATO</h3>
                    <p>{cabecalho.get('contato', 'NÃO INFORMADO')}</p>
                </div>
                <div class="info-card">
                    <h3>🔢 NÚMERO OP</h3>
                    <p>{cabecalho.get('numero_op', 'NÃO INFORMADO')}</p>
                </div>
                <div class="info-card">
                    <h3>📅 DATA</h3>
                    <p>{cabecalho.get('data', datetime.now().strftime('%d/%m/%Y'))}</p>
                </div>
                <div class="info-card">
                    <h3>📍 ENDEREÇO</h3>
                    <p>{cabecalho.get('endereco', 'NÃO INFORMADO')}</p>
                </div>
            </div>
            
            <div class="content">
                <h2>📦 MATERIAIS DIMENSIONADOS</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Qtd (OP)</th>
                            <th>Descrição</th>
                            <th>Material</th>
                            <th>Categoria</th>
                            <th>Unidade</th>
                            <th>Quantidade Calculada</th>
                            <th>Preço Unitário</th>
                            <th>Total (R$)</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for r in resultados:
        html += f"""
                        <tr>
                            <td>{r['codigo']}</td>
                            <td>{r['quantidade_op']}</td>
                            <td>{r['descricao']}</td>
                            <td>{r['material']}</td>
                            <td>{r['categoria']}</td>
                            <td>{r['unidade']}</td>
                            <td><strong>{r['quantidade_calculada']}</strong></td>
                            <td>R$ {r['preco_unitario']:.2f}</td>
                            <td><strong>R$ {r['total_material']:.2f}</strong></td>
                        </tr>
        """
    
    html += f"""
                    </tbody>
                </table>
                
                <div class="total">
                    <h2>💰 TOTAL GERAL: R$ {total_geral:.2f}</h2>
                </div>
                
                <div class="info-card" style="margin-top: 20px;">
                    <h3>📝 OBSERVAÇÕES</h3>
                    <p>{cabecalho.get('observacoes', 'Sem observações adicionais')}</p>
                </div>
            </div>
            
            <div class="footer">
                <p>Este relatório foi gerado automaticamente pelo Sistema de Dimensionamento Profissional</p>
                <p>Comunicação Visual - Todos os direitos reservados</p>
            </div>
        </div>
        
        <button class="btn-print" onclick="window.print()">🖨️ IMPRIMIR RELATÓRIO</button>
        
        <script>
            // Adiciona funcionalidade de impressão automática se desejar
            console.log("Relatório pronto para impressão");
        </script>
    </body>
    </html>
    """
    
    return html

# ==========================================
# INTERFACE PRINCIPAL STREAMLIT
# ==========================================

def main():
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/667eea/white?text=DIMENSIONA+VISUAL", use_container_width=False)
        st.markdown("## 🎯 Sistema Profissional")
        st.markdown("---")
        st.markdown("### 📋 Funcionalidades:")
        st.markdown("""
        - ✅ Leitura automática de PDF
        - ✅ Extração inteligente de medidas
        - ✅ Cálculo de todos os materiais
        - ✅ Relatório profissional
        - ✅ Impressão direta
        - ✅ Exportação de dados
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
        - Pintura e acabamento
        - Fixação e ferragens
        """)
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📐 SISTEMA PROFISSIONAL DE DIMENSIONAMENTO</h1>
        <p>Comunicação Visual - Cálculo Automático de Materiais</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload de arquivo
    uploaded_file = st.file_uploader(
        "📄 Envie o PDF da Ordem de Produção",
        type=["pdf"],
        help="Envie qualquer PDF de OP que o sistema extrairá automaticamente as medidas"
    )
    
    if uploaded_file is not None:
        with st.spinner("🔄 Processando PDF e calculando materiais..."):
            cabecalho, resultados, texto_raw = processar_pdf_completo(uploaded_file)
            
            if resultados and len(resultados) > 0:
                st.success(f"✅ Processado com sucesso! {len(resultados)} itens encontrados.")
                
                # Tabs para organização
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Materiais", "📈 Gráficos", "🖨️ Relatório"])
                
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
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Cliente:** {cabecalho.get('cliente', 'N/A')}")
                        st.write(f"**Local:** {cabecalho.get('local_instalacao', 'N/A')}")
                        st.write(f"**Contato:** {cabecalho.get('contato', 'N/A')}")
                    with col_b:
                        st.write(f"**OP Número:** {cabecalho.get('numero_op', 'N/A')}")
                        st.write(f"**Data:** {cabecalho.get('data', datetime.now().strftime('%d/%m/%Y'))}")
                        st.write(f"**Endereço:** {cabecalho.get('endereco', 'N/A')}")
                
                with tab2:
                    df = pd.DataFrame(resultados)
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Botão de exportação
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar CSV",
                        data=csv,
                        file_name=f"dimensionamento_{cabecalho.get('numero_op', 'relatorio')}.csv",
                        mime="text/csv"
                    )
                
                with tab3:
                    # Gráfico de materiais
                    df_cat = df.groupby("categoria")["total_material"].sum().reset_index()
                    fig = px.pie(df_cat, values="total_material", names="categoria", title="Distribuição por Categoria")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Gráfico de barras
                    df_mat = df.groupby("material")["quantidade_calculada"].sum().reset_index().head(10)
                    fig2 = px.bar(df_mat, x="material", y="quantidade_calculada", title="Top 10 Materiais por Quantidade")
                    st.plotly_chart(fig2, use_container_width=True)
                
                with tab4:
                    # Gera e exibe relatório HTML
                    html_relatorio = gerar_relatorio_html(cabecalho, resultados, uploaded_file.name)
                    st.components.v1.html(html_relatorio, height=600, scrolling=True)
                    
                    # Download do relatório
                    b64 = base64.b64encode(html_relatorio.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="relatorio_dimensionamento_{cabecalho.get("numero_op", "op")}.html" class="download-button">📥 Baixar Relatório Completo (HTML)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    st.info("💡 **Dica:** Clique em 'IMPRIMIR RELATÓRIO' no canto superior direito para gerar uma versão para impressão ou salvar como PDF.")
            
            else:
                st.error("❌ Não foi possível extrair itens do PDF. Verifique o formato do arquivo.")
    
    else:
        st.info("👈 **Envie um arquivo PDF** para começar o dimensionamento automático")
        
        # Exemplo de como funciona
        with st.expander("📖 Como funciona o sistema?"):
            st.markdown("""
            ### 🔍 Extração Automática de Medidas
            
            O sistema reconhece automaticamente:
            
            **Medidas de área:**
            - `61,93m²` → Adesivo/Lona
            - `2,22 x 1,70m` → Painel ACM
            - `60cm x 40cm` → Placa de sinalização
            
            **Letreiros:**
            - `15cm de altura de letra` → Letras em inox/acrílico
            
            **Totens e estruturas:**
            - `H=5 M` → Altura do totem
            - `diâmetro de 0,70m` → Placa redonda
            
            **Iluminação:**
            - `180 módulos de LED` → Quantidade de LEDs
            - `0,72 W` → Potência por módulo
            
            ### 📊 Resultados Gerados
            
            - Lista completa de materiais com quantidades calculadas
            - Cálculo de perdas (10-15% incluso)
            - Estimativa de custos
            - Relatório profissional para impressão
            - Exportação em CSV e HTML
            
            ### 🚀 Próximos Passos
            
            1. Envie qualquer PDF de OP
            2. Aguarde o processamento automático
            3. Revise os cálculos
            4. Exporte ou imprima o relatório
            """)

if __name__ == "__main__":
    main()