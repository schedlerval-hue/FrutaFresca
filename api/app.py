from flask import Flask, jsonify, send_from_directory, request, session, redirect
import sqlite3
import os
from datetime import datetime
from functools import wraps


# =====================================================
# CONFIGURAÇÕES
# =====================================================

app = Flask(__name__)

app.secret_key = "frutafresca_chave_secreta_2026"

SENHA_ADMIN = "fruta123"

LOCAL_RETIRADA = (
    "Av. Amazonas, 1815 - Universitário, Lajeado - RS, 95914-106"
)


# =====================================================
# CAMINHOS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

BANCO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "banco.db"
)


# =====================================================
# CONEXÃO COM O BANCO
# =====================================================

def conectar():

    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    return conexao


# =====================================================
# ADICIONAR COLUNA CASO NÃO EXISTA
# =====================================================

def adicionar_coluna_se_nao_existir(
    conexao,
    tabela,
    coluna,
    definicao
):

    colunas = conexao.execute(
        f"PRAGMA table_info({tabela})"
    ).fetchall()

    nomes = [
        coluna_info["name"]
        for coluna_info in colunas
    ]

    if coluna not in nomes:

        conexao.execute(
            f"""
            ALTER TABLE {tabela}
            ADD COLUMN {coluna} {definicao}
            """
        )


# =====================================================
# CRIAR BANCO
# =====================================================

def criar_banco():

    conexao = conectar()

    # -------------------------------------------------
    # TABELA DE PRODUTOS
    # -------------------------------------------------

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS produtos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo TEXT UNIQUE,

            nome TEXT NOT NULL,

            descricao TEXT,

            custo REAL DEFAULT 0,

            preco REAL NOT NULL,

            estoque REAL DEFAULT 0,

            imagem TEXT
        )
        """
    )


    # -------------------------------------------------
    # TABELA DE PEDIDOS
    # -------------------------------------------------

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS pedidos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome_cliente TEXT NOT NULL,

            telefone TEXT,

            forma_entrega TEXT DEFAULT 'Retirada',

            local_retirada TEXT,

            observacao TEXT,

            total REAL DEFAULT 0,

            data_pedido TEXT
        )
        """
    )


    # -------------------------------------------------
    # TABELA DE ITENS DO PEDIDO
    # -------------------------------------------------

    conexao.execute(
        """
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
        """
    )


    # -------------------------------------------------
    # GARANTIR COLUNAS ANTIGAS
    # -------------------------------------------------

    adicionar_coluna_se_nao_existir(
        conexao,
        "pedidos",
        "telefone",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "pedidos",
        "forma_entrega",
        "TEXT DEFAULT 'Retirada'"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "pedidos",
        "local_retirada",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "pedidos",
        "observacao",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "pedidos",
        "total",
        "REAL DEFAULT 0"
    )

    adicionar_coluna_se_nao_existir(
        conexao,
        "pedidos",
        "data_pedido",
        "TEXT"
    )


    # -------------------------------------------------
    # PRODUTOS INICIAIS
    #
    # Só cria se ainda não existirem.
    # Não repõe o estoque a cada inicialização.
    # -------------------------------------------------

    produtos_iniciais = [

        (
            "MORANGO",
            "Morango",
            "Morango fresco",
            0,
            45.00,
            10.00,
            "img/morango.jpg"
        ),

        (
            "UVA",
            "Uva",
            "Uva fresca",
            0,
            35.00,
            15.00,
            "img/uva.jpg"
        ),

        (
            "LARANJA",
            "Laranja",
            "Laranja fresca",
            0,
            8.99,
            20.00,
            "img/laranja.jpg"
        )

    ]


    for produto in produtos_iniciais:

        conexao.execute(
            """
            INSERT OR IGNORE INTO produtos
            (
                codigo,
                nome,
                descricao,
                custo,
                preco,
                estoque,
                imagem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            produto
        )


    conexao.commit()

    conexao.close()


# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

@app.route("/")
def inicio():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# =====================================================
# ARQUIVOS DO FRONTEND
# =====================================================

@app.route("/<path:arquivo>")
def arquivos_frontend(arquivo):

    return send_from_directory(
        FRONTEND_DIR,
        arquivo
    )


# =====================================================
# LISTAR PRODUTOS
# =====================================================

@app.route("/produtos", methods=["GET"])
def listar_produtos():

    conexao = conectar()

    produtos = conexao.execute(
        """
        SELECT
            id,
            codigo,
            nome,
            descricao,
            custo,
            preco,
            estoque,
            imagem
        FROM produtos
        ORDER BY id
        """
    ).fetchall()

    conexao.close()

    return jsonify([
        dict(produto)
        for produto in produtos
    ])


# =====================================================
# CRIAR PEDIDO
# =====================================================

@app.route("/pedidos", methods=["POST"])
def criar_pedido():

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "erro": "Nenhum dado foi enviado."
        }), 400


    nome_cliente = (
        dados.get("nome_cliente") or ""
    ).strip()

    telefone = (
        dados.get("telefone") or ""
    ).strip()

    forma_entrega = (
        dados.get("forma_entrega")
        or "Retirada"
    )

    local_retirada = (
        dados.get("local_retirada")
        or LOCAL_RETIRADA
    )

    observacao = (
        dados.get("observacao") or ""
    ).strip()

    itens = dados.get("itens", [])


    # -------------------------------------------------
    # VALIDAÇÕES
    # -------------------------------------------------

    if not nome_cliente:

        return jsonify({
            "sucesso": False,
            "erro": "Informe o nome do cliente."
        }), 400


    if not telefone:

        return jsonify({
            "sucesso": False,
            "erro": "Informe o telefone."
        }), 400


    if not isinstance(itens, list) or len(itens) == 0:

        return jsonify({
            "sucesso": False,
            "erro": "O pedido precisa ter pelo menos um produto."
        }), 400


    conexao = conectar()


    try:

        produtos_pedido = []

        total = 0


        # -------------------------------------------------
        # VERIFICAR TODOS OS PRODUTOS E ESTOQUES
        # ANTES DE CRIAR O PEDIDO
        # -------------------------------------------------

        for item in itens:

            try:

                produto_id = int(
                    item.get("produto_id")
                )

                quantidade = float(
                    item.get("quantidade_kg")
                )

            except (TypeError, ValueError):

                conexao.rollback()

                return jsonify({
                    "sucesso": False,
                    "erro": "Produto ou quantidade inválida."
                }), 400


            if quantidade <= 0:

                conexao.rollback()

                return jsonify({
                    "sucesso": False,
                    "erro": "A quantidade deve ser maior que zero."
                }), 400


            produto = conexao.execute(
                """
                SELECT
                    id,
                    nome,
                    preco,
                    estoque
                FROM produtos
                WHERE id = ?
                """,
                (produto_id,)
            ).fetchone()


            if not produto:

                conexao.rollback()

                return jsonify({
                    "sucesso": False,
                    "erro":
                        f"Produto {produto_id} não encontrado."
                }), 404


            estoque_atual = float(
                produto["estoque"] or 0
            )

            preco = float(
                produto["preco"] or 0
            )


            # -------------------------------------------------
            # VERIFICAR ESTOQUE
            # -------------------------------------------------

            if quantidade > estoque_atual:

                conexao.rollback()

                return jsonify({

                    "sucesso": False,

                    "erro":
                        f"Estoque insuficiente para "
                        f"{produto['nome']}. "
                        f"Disponível: "
                        f"{estoque_atual:.2f} kg."
                }), 400


            subtotal = quantidade * preco

            total += subtotal


            produtos_pedido.append({

                "produto_id": produto_id,

                "nome": produto["nome"],

                "quantidade": quantidade,

                "preco": preco,

                "subtotal": subtotal,

                "estoque_atual": estoque_atual

            })


        # -------------------------------------------------
        # CRIAR PEDIDO
        # -------------------------------------------------

        data_pedido = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        cursor = conexao.execute(
            """
            INSERT INTO pedidos
            (
                nome_cliente,
                telefone,
                forma_entrega,
                local_retirada,
                observacao,
                total,
                data_pedido
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome_cliente,
                telefone,
                forma_entrega,
                local_retirada,
                observacao,
                total,
                data_pedido
            )
        )


        pedido_id = cursor.lastrowid


        # -------------------------------------------------
        # SALVAR ITENS E BAIXAR ESTOQUE
        # -------------------------------------------------

        for produto in produtos_pedido:

            conexao.execute(
                """
                INSERT INTO itens_pedido
                (
                    pedido_id,
                    produto_id,
                    quantidade_kg,
                    preco_kg,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    produto["produto_id"],
                    produto["quantidade"],
                    produto["preco"],
                    produto["subtotal"]
                )
            )


            novo_estoque = (
                produto["estoque_atual"]
                - produto["quantidade"]
            )


            if novo_estoque < 0:
                novo_estoque = 0


            conexao.execute(
                """
                UPDATE produtos

                SET estoque = ?

                WHERE id = ?
                """,
                (
                    novo_estoque,
                    produto["produto_id"]
                )
            )


        # -------------------------------------------------
        # SALVAR NO BANCO
        # -------------------------------------------------

        conexao.commit()


        return jsonify({

            "sucesso": True,

            "pedido_id": pedido_id,

            "total": total,

            "local_retirada": local_retirada,

            "mensagem":
                "Pedido realizado com sucesso!"

        }), 201


    except Exception as erro:

        conexao.rollback()

        print(
            "ERRO AO CRIAR PEDIDO:",
            erro
        )

        return jsonify({

            "sucesso": False,

            "erro":
                "Não foi possível finalizar o pedido."
        }), 500


    finally:

        conexao.close()


# =====================================================
# LOGIN ADMIN
# =====================================================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        senha = request.form.get(
            "senha",
            ""
        )

        if senha == SENHA_ADMIN:

            session["admin"] = True

            return redirect(
                "/relatorio/mensal"
            )

        return """
        <h2>Senha incorreta</h2>
        <a href="/admin">Voltar</a>
        """


    return """
    <!DOCTYPE html>

    <html lang="pt-BR">

    <head>

        <meta charset="UTF-8">

        <title>
            Administração - Fruta Fresca
        </title>

    </head>

    <body>

        <h1>
            Área administrativa
        </h1>

        <form method="POST">

            <label>
                Senha:
            </label>

            <input
                type="password"
                name="senha"
                required
            >

            <button type="submit">
                Entrar
            </button>

        </form>

    </body>

    </html>
    """


# =====================================================
# PROTEGER ÁREA ADMINISTRATIVA
# =====================================================

def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):

            return redirect("/admin")

        return func(*args, **kwargs)

    return wrapper


# =====================================================
# RELATÓRIO MENSAL
# =====================================================

@app.route("/relatorio/mensal")
@admin_required
def relatorio_mensal():

    conexao = conectar()


    pedidos = conexao.execute(
        """
        SELECT
            id,
            nome_cliente,
            telefone,
            forma_entrega,
            local_retirada,
            observacao,
            total,
            data_pedido
        FROM pedidos
        ORDER BY id DESC
        """
    ).fetchall()


    itens = conexao.execute(
        """
        SELECT
            itens_pedido.pedido_id,
            itens_pedido.quantidade_kg,
            itens_pedido.preco_kg,
            itens_pedido.subtotal,
            produtos.nome

        FROM itens_pedido

        INNER JOIN produtos
            ON produtos.id =
               itens_pedido.produto_id

        ORDER BY itens_pedido.pedido_id DESC
        """
    ).fetchall()


    conexao.close()


    html = """
    <!DOCTYPE html>

    <html lang="pt-BR">

    <head>

        <meta charset="UTF-8">

        <title>
            Relatório Mensal - Fruta Fresca
        </title>

        <style>

            body {
                font-family: Arial, sans-serif;
                margin: 30px;
            }

            h1 {
                margin-bottom: 30px;
            }

            .pedido {
                border: 1px solid #ddd;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 10px;
            }

            .item {
                margin-left: 20px;
                margin-top: 8px;
            }

            .total {
                font-weight: bold;
                margin-top: 15px;
            }

            .sair {
                display: inline-block;
                margin-bottom: 20px;
            }

        </style>

    </head>

    <body>

        <a
            class="sair"
            href="/admin/logout"
        >
            Sair
        </a>

        <h1>
            Relatório de pedidos
        </h1>
    """


    for pedido in pedidos:

        html += f"""
        <div class="pedido">

            <h2>
                Pedido nº {pedido["id"]}
            </h2>

            <p>
                <strong>Cliente:</strong>
                {pedido["nome_cliente"]}
            </p>

            <p>
                <strong>Telefone:</strong>
                {pedido["telefone"] or "-"}
            </p>

            <p>
                <strong>Data:</strong>
                {pedido["data_pedido"] or "-"}
            </p>

            <p>
                <strong>Retirada:</strong>
                {pedido["local_retirada"] or "-"}
            </p>

            <p>
                <strong>Observação:</strong>
                {pedido["observacao"] or "-"}
            </p>

            <h3>
                Produtos
            </h3>
        """


        for item in itens:

            if item["pedido_id"] == pedido["id"]:

                html += f"""
                <div class="item">

                    {item["nome"]}

                    -
                    {item["quantidade_kg"]:.2f} kg

                    -
                    R$ {item["subtotal"]:.2f}

                </div>
                """


        html += f"""

            <p class="total">

                Total:
                R$ {pedido["total"]:.2f}

            </p>

        </div>
        """


    html += """
    </body>

    </html>
    """


    return html


# =====================================================
# LOGOUT
# =====================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect("/admin")


# =====================================================
# INICIAR APLICAÇÃO
# =====================================================

if __name__ == "__main__":

    criar_banco()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )