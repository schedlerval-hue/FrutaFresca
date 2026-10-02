import sqlite3


# ==========================================
# CONEXÃO COM O BANCO
# ==========================================

def conectar():
    conexao = sqlite3.connect("banco.db")
    conexao.row_factory = sqlite3.Row
    return conexao


# ==========================================
# CRIAÇÃO DAS TABELAS
# ==========================================

def criar_tabelas():

    conexao = conectar()

    # --------------------------------------
    # TABELA DE PRODUTOS
    # --------------------------------------

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            estoque REAL NOT NULL,
            imagem TEXT
        )
    """)


    # --------------------------------------
    # TABELA DE PEDIDOS
    # --------------------------------------

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            forma_entrega TEXT NOT NULL,
            cidade TEXT NOT NULL,
            bairro TEXT NOT NULL,
            rua TEXT NOT NULL,
            numero TEXT NOT NULL,
            complemento TEXT,
            observacao TEXT,
            total REAL NOT NULL,
            data_pedido TEXT NOT NULL
        )
    """)


    # --------------------------------------
    # ITENS DO PEDIDO
    # --------------------------------------

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade_kg REAL NOT NULL,
            preco_kg REAL NOT NULL,
            subtotal REAL NOT NULL,

            FOREIGN KEY (pedido_id)
                REFERENCES pedidos(id),

            FOREIGN KEY (produto_id)
                REFERENCES produtos(id)
        )
    """)


    conexao.commit()

    conexao.close()

    print("Banco de dados criado com sucesso!")


# ==========================================
# EXECUTAR
# ==========================================

if __name__ == "__main__":
    criar_tabelas()