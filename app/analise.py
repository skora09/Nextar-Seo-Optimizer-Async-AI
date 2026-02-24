import streamlit as st
import pandas as pd
import json
import openai
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurações iniciais
st.set_page_config(page_title="Nextar SEO Analytics", layout="wide")
client = openai.OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def processar_com_llm(row):
    prompt = f"""
    Otimize o produto para SEO:

    Nome: {row['Nome_Produto']}
    Categoria: {row['Categoria']}
    Descrição: {row['Descricao_Original']}
    """

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "produto_seo",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "novo_titulo": {"type": "string"},
                            "nova_descricao": {"type": "string"},
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["novo_titulo", "nova_descricao", "keywords"]
                    }
                }
            }
        )

        conteudo = response.choices[0].message.content.strip()

        if not conteudo:
            raise ValueError("Resposta vazia do modelo.")

        return json.loads(conteudo)

    except Exception as e:
        st.warning(f"Erro ao processar {row['Nome_Produto']}: {e}")
        return None

st.title("🚀 Nextar SEO Optimizer & Data Intelligence")

uploaded_file = st.file_uploader("Upload do CSV Nextar", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Amostra dos dados:", df.head(2))

    if st.button("Executar Inteligência de Dados"):
        resultados = []
        progresso = st.progress(0)
        
        max_threads = 4  # pode testar 3, 4 ou 5

        def processar_row(index_row):
            i, row = index_row
            res = processar_com_llm(row)
            if res:
                score_antigo = len(row['Descricao_Original']) / 2
                score_novo = len(res['nova_descricao']) / 1.5

                return {
                    **row,
                    **res,
                    "score_antigo": score_antigo,
                    "score_novo": score_novo,
                    "melhoria": ((score_novo - score_antigo) / score_antigo) * 100
                }
            return None


        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {
                executor.submit(processar_row, item): item[0]
                for item in df.iterrows()
            }

            for count, future in enumerate(as_completed(futures)):
                result = future.result()
                if result:
                    resultados.append(result)

                progresso.progress((count + 1) / len(df))

        # --- A SOLUÇÃO PARA O KEYERROR ---
        if resultados:
            df_final = pd.DataFrame(resultados)
            
            # Dashboard de métricas
            c1, c2 = st.columns(2)
            c1.metric("Melhoria Média de SEO", f"{df_final['melhoria'].mean():.1f}%")
            c2.metric("Sucesso de Processamento", f"{(len(df_final)/len(df))*100:.0f}%")
            
            # Gráfico de barras
            fig = px.bar(df_final, x="Nome_Produto", y="melhoria", title="Impacto da IA por Produto (%)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df_final)
        else:
            st.error("Nenhum dado foi processado. Verifique se o LM Studio está no ar (Local Server -> Start Server).")