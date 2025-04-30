import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from BancoDeDados import salvar_artigo

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

# Exemplo de termos
termos = [
        "Hospital das Clínicas - UFPE",
        "HC UFPE",
        "Universidade Federal de Pernambuco hospital",
        "pesquisadores HC UFPE"
    ]
processar_artigos_e_salvar(termos)
