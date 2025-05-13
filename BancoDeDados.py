
import pandas as pd

def salvar_artigo(titulo, autores, resumo, data_publicacao, link):
    # Exemplo de lista com os dados coletados
    Artigos = [
        {
            "titulo": titulo,
            "autores": autores,
            "resumo": resumo,
            "data_publicacao": data_publicacao,
            "link": link
        }
        
    ]
    # Cria o DataFrame
    df = pd.DataFrame(Artigos)

    # Exporta para Excel
    df.to_excel("Artigos.xlsx", index=False)




    
