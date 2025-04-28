import sqlite3

banco = sqlite3.connect("Artigos_HCufpe.db")

cursor = banco.cursor()

cursor.execute()

cursor.execute("CREATE TABLE Artigos(Titulo text, Autores text, Resumo text, Data de publicação integer, link de acesso text)")

