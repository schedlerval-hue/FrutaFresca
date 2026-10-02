from database import conectar


def listar_produtos():
    conexao = conectar()

    produtos = conexao.execute("""
        SELECT * FROM produtos
        ORDER BY id
    """).fetchall()

    conexao.close()

    return produtos


def buscar_produto(codigo):
    conexao = conectar()

    produto = conexao.execute("""
        SELECT * FROM produtos
        WHERE codigo = ?
    """, (codigo,)).fetchone()

    conexao.close()

    return produto


def cadastrar_produto(codigo, nome, descricao, custo, preco, estoque, imagem):
    conexao = conectar()

    conexao.execute("""
        INSERT INTO produtos
        (codigo, nome, descricao, custo, preco, estoque, imagem)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (codigo, nome, descricao, custo, preco, estoque, imagem))

    conexao.commit()
    conexao.close()