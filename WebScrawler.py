import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from BancoDeDados import salvar_artigo

df = pd.read_excel("Termos de Busca.xlsx")

SCOPUS_API_KEY = "c3518a1d259d7b6709aacc9a660c2980"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def buscar_artigos_google_academico(termo_pesquisa, limite=5):
    base_url = "https://scholar.google.com/scholar"
    params = {"q": termo_pesquisa, "hl": "pt-BR"}
    url = f"{base_url}?{urlencode(params)}"

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    resultados = soup.select(".gs_r")[:limite]

    artigos = []
    for r in resultados:
        try:
            titulo = r.select_one(".gs_rt").text
            link = r.select_one(".gs_rt a")["href"] if r.select_one(".gs_rt a") else "Link indisponível"
            autores_info = r.select_one(".gs_a").text
            resumo = r.select_one(".gs_rs").text if r.select_one(".gs_rs") else "Resumo indisponível"

            artigo = {
                "titulo": titulo,
                "autores": autores_info,
                "resumo": resumo,
                "data_publicacao": "Desconhecida",  # Google Scholar não fornece a data diretamente
                "link": link
            }

            artigos.append(artigo)
        except Exception as e:
            print(f"[!] Erro ao extrair resultado: {e}")
            continue

    return artigos


            
def buscar_artigos_scopus(termo_pesquisa, limite=5): #LIMITE PARA USAR COMO EXEMPLIFICAÇÃO
    print(f"🔍 Buscando por: {termo_pesquisa}")
    
    base_url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "Accept": "application/json",
        "X-ELS-APIKey": SCOPUS_API_KEY
    }
    params = {
        "query": f'TITLE-ABS-KEY("{termo_pesquisa}")',
        "count": limite
    }

    response = requests.get(base_url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    artigos = []
    for item in data.get("search-results", {}).get("entry", []):
        artigo = {
            "titulo": item.get("dc:title", "Título indisponível"),
            "autores": item.get("dc:creator", "Autor(es) indisponíveis"),
            "resumo": item.get("dc:description", "Resumo indisponível"),
            "data_publicacao": item.get("prism:coverDate", "Data desconhecida"),
            "link": item.get("prism:doi", "Link indisponível")
        }
        if artigo["link"] != "Link indisponível":
            artigo["link"] = f'https://doi.org/{artigo["link"]}'
        artigos.append(artigo)

    return artigos
    
#Busca Artigos no SciELO:
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def buscar_artigos_scielo(lista_termos, max_resultados=5):
    base_url = "https://search.scielo.org/"
    todos_resultados = []

    for termo in lista_termos:
        print(f"\n🔍 Buscando por: '{termo}'")
        params = {
            "q": termo,
            "lang": "pt",
            "count": max_resultados,
        }

        resposta = requests.get(base_url, params=params)
        soup = BeautifulSoup(resposta.text, "html.parser")

        for artigo in soup.select(".item"):
            titulo = artigo.select_one(".title").text.strip() if artigo.select_one(".title") else "Sem título"
            autores = artigo.select_one(".authors").text.strip() if artigo.select_one(".authors") else "Desconhecidos"
            data = artigo.select_one(".date").text.strip() if artigo.select_one(".date") else "Data não encontrada"
            link = artigo.select_one("a")["href"] if artigo.select_one("a") else "Sem link"

            resumo = "Resumo não encontrado"
            try:
                art_resposta = requests.get(link)
                art_soup = BeautifulSoup(art_resposta.text, "html.parser")
                resumo_tag = art_soup.select_one("div.abstract, div#abstract")
                if resumo_tag:
                    resumo = resumo_tag.text.strip()
            except:
                pass

            todos_resultados.append({
                "termo_busca": termo,
                "titulo": titulo,
                "autores": autores,
                "data": data,
                "resumo": resumo,
                "link": link
            })

    return todos_resultados


def processar_artigos_e_salvar(termos_de_busca):
    for termo in termos_de_busca:
        print(f"🔍 Buscando artigos para: {termo}")
        
        artigos = buscar_artigos_google_academico(termo)
        for artigo in artigos:
            salvar_artigo(
                titulo=artigo["titulo"],
                autores=artigo["autores"],
                resumo=artigo["resumo"],
                data_publicacao=artigo["data_publicacao"],
                link=artigo["link"]
            )
            # print(artigo["titulo"] + "\n",
            #       artigo["autores"],"\n",
            #       artigo["link"]
            #       )
        
        artigos_scopus = buscar_artigos_scopus(termo)
        for artigo in artigos_scopus:
            salvar_artigo(
                titulo=artigo["titulo"],
                autores=artigo["autores"],
                resumo=artigo["resumo"],
                data_publicacao=artigo["data_publicacao"],
                link=artigo["link"]
            )
            # print(artigo["titulo"], "\n",
            #       artigo["autores"], "\n",
            #       artigo["link"], "\n")
        artigos_scielo = buscar_artigos_scielo(termo)
        for artigo in artigos_scielo:
            salvar_artigo(
                titulo=artigo["titulo"],
                autores=artigo["autores"],
                resumo=artigo["resumo"],
                data_publicacao=artigo["data_publicacao"],
                link=artigo["link"]
            )
            print(artigo["titulo"], "\n",
                  artigo["autores"], "\n",
                  artigo["link"], "\n")



# Exemplo de termos
termos = df.iloc[:, 0].dropna().astype(str).tolist()
processar_artigos_e_salvar(termos)


