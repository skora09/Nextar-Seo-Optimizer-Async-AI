import pandas as pd

def criar_base_simulada():
    dados = [
        {
            "Nome_Produto": "Tenis Corrida Performance 2026",
            "Categoria": "Calçados",
            "Descricao_Original": "tenis confortavel para correr",
            "Preco": 459.90
        },
        {
            "Nome_Produto": "Camiseta Algodao Organico Curitiba",
            "Categoria": "Vestuário",
            "Descricao_Original": "camiseta branca basica 100% algodao",
            "Preco": 89.00
        },
        {
            "Nome_Produto": "Smartwatch Pro Max V5",
            "Categoria": "Eletrônicos",
            "Descricao_Original": "relogio inteligente com bluetooth",
            "Preco": 1200.00
        }
    ]
    
    df = pd.DataFrame(dados)
    df.to_csv("produtos_nextar.csv", index=False)
    print("✅ Arquivo 'produtos_nextar.csv' gerado com sucesso!")

if __name__ == "__main__":
    criar_base_simulada()