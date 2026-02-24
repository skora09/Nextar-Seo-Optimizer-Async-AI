import streamlit as st
import pandas as pd
import json
import plotly.express as px
import asyncio
import aiohttp
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import tempfile

# ==================================
# CONFIG
# ==================================

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "local-model"
MAX_CONCORRENCIA = 4

st.set_page_config(page_title="Nextar SEO Analytics", layout="wide")


# LIMPEZA JSON


def extrair_json(texto):
    if not texto:
        return None

    texto = texto.strip()

    # Remove blocos ```json ```
    if "```" in texto:
        texto = texto.split("```")[1]

    # Extrai somente trecho entre { }
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        texto = match.group()

    try:
        return json.loads(texto)
    except:
        return None


# CHAMADA ASSÍNCRONA


async def chamar_llm(session, semaphore, row):

    prompt = f"""
    Você é um SEO profissional nivel senior, pegue essas informações e crie o SEO perfeito e personalizado para o item baseado em mercado, marketing e tecnicas infaliveis de vendas:

    Nome: {row['Nome_Produto']}
    Categoria: {row['Categoria']}
    Descrição: {row['Descricao_Original']}

    Responda apenas com JSON:
    {{
        "novo_titulo": "...",
        "nova_descricao": "...",
        "keywords": ["a","b"]
    }}
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    async with semaphore:
        async with session.post(LM_STUDIO_URL, json=payload) as resp:
            data = await resp.json()

    try:
        conteudo = data["choices"][0]["message"]["content"]
        resultado = extrair_json(conteudo)
        return resultado
    except:
        return None


# PDF


def limpar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return re.sub(r'\s+', ' ', texto).strip()

def gerar_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    pdf.add_font("DejaVu", "", "DejaVuSans.ttf")
    pdf.set_font("DejaVu", size=14)

    pdf.cell(0, 10,
             "Relatorio SEO - Antes vs Depois",
             new_x=XPos.LMARGIN,
             new_y=YPos.NEXT)

    pdf.set_font("DejaVu", size=10)
    pdf.ln(10)

    for _, row in df.iterrows():

        pdf.set_font("DejaVu", size=12)
        pdf.multi_cell(pdf.w - 20, 6,
            f"Produto: {limpar_texto(row['Nome_Produto'])}"
        )

        pdf.ln(2)

        antes = (
            f"ANTES:\n"
            f"Título: {limpar_texto(row['Nome_Produto'])}\n"
            f"Descrição: {limpar_texto(row['Descricao_Original'])}"
        )

        depois = (
            f"DEPOIS:\n"
            f"Novo Título: {limpar_texto(row['novo_titulo'])}\n"
            f"Nova Descrição: {limpar_texto(row['nova_descricao'])}\n"
            f"Keywords: {', '.join(row['keywords'])}\n"
            f"Melhoria SEO: {row['melhoria']:.2f}%"
        )

        pdf.set_font("DejaVu", size=10)
        pdf.multi_cell(pdf.w - 20, 6, antes)
        pdf.ln(2)
        pdf.multi_cell(pdf.w - 20, 6, depois)

        pdf.ln(18)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name


# STREAMLIT


st.title("Projeto Nextar")

uploaded_file = st.file_uploader("Upload do CSV", type="csv")

if uploaded_file:

    df = pd.read_csv(uploaded_file)
    st.write(df.head(2))

    if st.button("Executar IA"):

        semaphore = asyncio.Semaphore(MAX_CONCORRENCIA)
        resultados = []

        async def processar():

            async with aiohttp.ClientSession() as session:

                tarefas = [
                    chamar_llm(session, semaphore, row)
                    for _, row in df.iterrows()
                ]

                respostas = await asyncio.gather(*tarefas)

                for (idx, r), res in zip(df.iterrows(), respostas):
                    if res:

                        score_antigo = len(r['Descricao_Original']) / 2
                        score_novo = len(res['nova_descricao']) / 1.5

                        resultados.append({
                            **r,
                            **res,
                            "score_antigo": score_antigo,
                            "score_novo": score_novo,
                            "melhoria": ((score_novo - score_antigo) / score_antigo) * 100
                        })

        asyncio.run(processar())

        if resultados:

            df_final = pd.DataFrame(resultados)

            st.metric("Melhoria Média",
                      f"{df_final['melhoria'].mean():.1f}%")

            fig = px.bar(
                df_final,
                x="Nome_Produto",
                y="melhoria",
                title="Impacto da IA"
            )

            st.plotly_chart(fig, width="stretch")

            st.dataframe(df_final)

            pdf_path = gerar_pdf(df_final)

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Baixar PDF",
                    f,
                    file_name="relatorio_seo.pdf",
                    mime="application/pdf"
                )

        else:
            st.error("Nenhum dado processado.")