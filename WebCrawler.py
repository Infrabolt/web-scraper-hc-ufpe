import threading
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from xml.etree import ElementTree
import customtkinter as ctk
from tkinter import messagebox

# --- Configurações de tema ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

SCOPUS_API_KEY = "c3518a1d259d7b6709aacc9a660c2980"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
}

# --- Funções de busca ---
def buscar_artigos_google_academico(termo, limite=5):
    url = f"https://scholar.google.com/scholar?{urlencode({'q': termo, 'hl': 'pt-BR'})}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return [f"[Google Scholar] Erro na requisição: {e}"]
    if "accounts.google.com/Sorry" in r.url:
        return ["[Google Scholar] Bloqueado por CAPTCHA ou similar."]
    soup = BeautifulSoup(r.text, "html.parser")
    blocos = soup.select("div.gs_ri")[:limite]
    artigos = []
    for b in blocos:
        try:
            h3 = b.find('h3', class_='gs_rt')
            if h3 and h3.a:
                titulo = h3.a.text.strip()
                link = h3.a['href']
            else:
                titulo = h3.text.strip() if h3 else "Título indisponível"
                link = "Link indisponível"
            autores = b.find('div', class_='gs_a').text.strip() if b.find('div', 'gs_a') else "Autor(es) indisponíveis"
            resumo = b.find('div', class_='gs_rs').text.strip() if b.find('div', 'gs_rs') else "Resumo indisponível"
            artigos.append({
                "titulo": titulo,
                "autores": autores,
                "data_publicacao": "Desconhecida",
                "resumo": resumo,
                "link": link
            })
        except Exception as e:
            artigos.append(f"[Google Scholar] Erro: {e}")
    return artigos


def buscar_artigos_scopus(termo, limite=5):
    try:
        resp = requests.get(
            "https://api.elsevier.com/content/search/scopus",
            headers={"Accept": "application/json", "X-ELS-APIKey": SCOPUS_API_KEY},
            params={"query": f'TITLE-ABS-KEY("{termo}")', "count": limite}
        )
        resp.raise_for_status()
        data = resp.json()
        artigos = []
        for item in data.get('search-results', {}).get('entry', [])[:limite]:
            artigos.append({
                'titulo': item.get('dc:title', 'Título indisponível'),
                'autores': item.get('dc:creator', 'Autor(es) indisponíveis'),
                'data_publicacao': item.get('prism:coverDate', 'Data desconhecida'),
                'resumo': item.get('dc:description', 'Resumo indisponível'),
                'link': f"https://doi.org/{item['prism:doi']}" if 'prism:doi' in item else 'Link indisponível'
            })
        return artigos
    except Exception as e:
        return [f"[Scopus] Erro: {e}"]


def buscar_artigos_scielo(termos, limite=5):
    resultados = []
    for termo in termos:
        try:
            resp = requests.get(
                "https://search.scielo.org/",
                params={"q": termo, "lang": "pt", "count": limite}
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for art in soup.select('.item')[:limite]:
                titulo = art.select_one('.title').text.strip() if art.select_one('.title') else 'Sem título'
                autores = art.select_one('.authors').text.strip() if art.select_one('.authors') else 'Desconhecidos'
                data = art.select_one('.date').text.strip() if art.select_one('.date') else 'Data não encontrada'
                link = art.a['href'] if art.a else 'Sem link'
                resumo = 'Resumo não encontrado'
                try:
                    r2 = requests.get(link)
                    r2.raise_for_status()
                    tag = BeautifulSoup(r2.text, 'html.parser').select_one('div.abstract,div#abstract')
                    if tag:
                        resumo = tag.text.strip()
                except:
                    pass
                resultados.append({
                    'titulo': titulo,
                    'autores': autores,
                    'data_publicacao': data,
                    'resumo': resumo,
                    'link': link
                })
        except Exception as e:
            resultados.append({
                'titulo': f'[SciELO] Erro: {e}'
            })
    return resultados


def buscar_artigos_pubmed(termo, inicio='1980', fim='2025', limite=5):
    base = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    try:
        r1 = requests.get(base + 'esearch.fcgi', params={
            'db': 'pubmed', 'term': termo, 'retmax': limite,
            'retmode': 'xml', 'mindate': inicio, 'maxdate': fim
        })
        r1.raise_for_status()
        ids = [x.text for x in ElementTree.fromstring(r1.content).findall('.//Id')][:limite]
        if not ids:
            return []
        r2 = requests.get(base + 'efetch.fcgi', params={
            'db': 'pubmed', 'id': ','.join(ids), 'retmode': 'xml'
        })
        r2.raise_for_status()
        arts = []
        for art in ElementTree.fromstring(r2.content).findall('.//PubmedArticle'):
            try:
                titulo = art.findtext('.//ArticleTitle')
                autores = ','.join([
                    f"{a.findtext('ForeName')} {a.findtext('LastName')}" for a in art.findall('.//Author')
                    if a.findtext('ForeName') and a.findtext('LastName')
                ])
                data_pub = art.findtext('.//PubDate/Year') or 'Data desconhecida'
                link = f"https://pubmed.ncbi.nlm.nih.gov/{art.findtext('.//PMID')}"
                resumo = art.findtext('.//AbstractText') or 'Resumo indisponível'
                arts.append({
                    'titulo': titulo,
                    'autores': autores,
                    'data_publicacao': data_pub,
                    'resumo': resumo,
                    'link': link
                })
            except:
                pass
        return arts
    except Exception as e:
        return [f"[PubMed] Erro: {e}"]


def processar(termos, limite):
    log_box.configure(state='normal')
    log_box.delete('0.0', ctk.END)
    all_artigos = []
    for t in termos:
        log_box.insert(ctk.END, f"\n===== {t} =====\n")
        for fonte, fn in [
            ('Google Scholar', buscar_artigos_google_academico),
            ('Scopus', buscar_artigos_scopus),
            ('SciELO', lambda termo, lim: buscar_artigos_scielo([termo], lim)),
            ('PubMed', lambda termo, lim: buscar_artigos_pubmed(termo, limite=lim))
        ]:
            for item in fn(t, limite):
                if isinstance(item, dict):
                    log_box.insert(ctk.END, f"[{fonte}] {item['titulo']}\n")
                    all_artigos.append(item)
                else:
                    log_box.insert(ctk.END, f"{item}\n")
    if all_artigos:
        pd.DataFrame(all_artigos).to_excel('Artigos.xlsx', index=False)
        log_box.insert(ctk.END, "\n✅ Artigos.xlsx salvo.\n")
    else:
        log_box.insert(ctk.END, "\n⚠️ Nenhum artigo encontrado.\n")
    log_box.configure(state='disabled')

# --- GUI CustomTkinter ---
root = ctk.CTk()
root.title('Buscador de Artigos')
frm = ctk.CTkFrame(root)
frm.pack(pady=10)

# Entrada de limite
txt_limite = ctk.CTkEntry(frm, placeholder_text='Limite de resultados', width=150)
txt_limite.grid(row=0, column=0, padx=5)

btn_buscar = ctk.CTkButton(
    frm, text='Buscar artigos',
    command=lambda: threading.Thread(target=task, daemon=True).start()
)
btn_buscar.grid(row=0, column=1, padx=5)

btn_sair = ctk.CTkButton(frm, text='Sair', command=root.destroy)
btn_sair.grid(row=0, column=2, padx=5)

log_box = ctk.CTkTextbox(root, width=800, height=400)
log_box.pack(padx=20, pady=10)
log_box.configure(state='disabled')

# Função para iniciar processo com limite lido da GUI
def task():
    try:
        df = pd.read_excel('Termos de Busca.xlsx')
        termos = df.iloc[:,0].dropna().astype(str).tolist()
        if not termos:
            messagebox.showwarning('Aviso', 'Nenhum termo na planilha.')
            return
    except FileNotFoundError:
        messagebox.showerror('Erro', 'Termos de Busca.xlsx não encontrado.')
        return
    try:
        limite = int(txt_limite.get())
        if limite < 1:
            raise ValueError
    except:
        messagebox.showerror('Erro', 'Informe um limite válido (inteiro ≥1).')
        return
    processar(termos, limite)

root.mainloop()