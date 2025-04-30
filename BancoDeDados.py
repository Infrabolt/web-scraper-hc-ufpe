import sqlite3

def CriarBanco():
    banco = sqlite3.connect("Artigos_HCufpe.db")

    cursor = banco.cursor()

    cursor.execute("SELECT 1")  # só testando a conexão

    cursor.execute("CREATE TABLE Artigos(Titulo text, Autores text, Resumo text, Data de publicação integer, link de acesso text)")

    # excluir duplicatas
    cursor.execute("DELETE FROM Artigos WHERE rowid NOT IN (SELECT MIN(rowid) FROM Artigos GROUP BY Titulo, Autores, Resumo, [Data de publicação], [link de acesso])")

    banco.commit()
    banco.close()

def salvar_artigo(titulo, autores, resumo, data_publicacao, link):
    return