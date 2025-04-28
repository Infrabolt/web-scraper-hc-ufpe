import os
import requests
from bs4 import BeautifulSoup
import openai
from BancoDeDados import salvar_resumo  # função esperada para salvar no banco

# Configure sua chave de API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def extrair_texto_principal(url: str) -> str:
    """
    Dado um URL de artigo, faz fetch da página e extrai o texto principal
    (título + parágrafos).
    """
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Exemplo genérico: considera <article> ou <div class="content">
    content = soup.find("article") or soup.find("div", class_="content")
    if not content:
        # fallback: todos <p>
        paragraphs = soup.find_all("p")
    else:
        paragraphs = content.find_all("p")
    
    texto = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
    return texto

def gerar_resumo_via_openai(texto: str) -> str:
    """
    Gera resumo do texto usando a API de chat completions da OpenAI.
    """
    prompt = (
        "Resuma o seguinte texto de artigo científico em até 150 palavras, "
        "mantendo os conceitos-chave e estruturas principais:\n\n" + texto
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um assistente que gera resumos científicos claros e concisos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )
    resumo = response.choices[0].message.content.strip()
    return resumo

def processar_e_salvar_resumo(url: str):
    """
    Função principal: recebe um link, extrai texto, gera resumo e salva no banco.
    """
    print(f"Iniciando processamento do artigo: {url}")
    
    # 1. Extrair conteúdo
    texto = extrair_texto_principal(url)
    if not texto:
        raise ValueError("Não foi possível extrair conteúdo do artigo.")
    
    # 2. Gerar resumo
    resumo = gerar_resumo_via_openai(texto)
    print("Resumo gerado com sucesso.")
    
    # 3. Salvar via módulo BancoDeDados
    salvar_resumo(url=url, resumo=resumo)
    print("Resumo salvo no banco de dados com sucesso.")

# Exemplo de uso:
if __name__ == "__main__":
    artigo_url = "https://exemplo.com/seu-artigo-cientifico"
    processar_e_salvar_resumo(artigo_url)