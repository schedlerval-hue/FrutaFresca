import sqlite3

conexao = sqlite3.connect("banco.db")

comandos = """
UPDATE produtos
SET preco = 45.00
WHERE codigo = '001';

UPDATE produtos
SET preco = 35.00
WHERE codigo = '002';

UPDATE produtos
SET preco = 8.99
WHERE codigo = '003';
"""

conexao.executescript(comandos)

conexao.commit()
conexao.close()

print("Preços atualizados com sucesso!")