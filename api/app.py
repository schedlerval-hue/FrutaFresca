from flask import Flask, jsonify, send_from_directory, request, session, redirect
import sqlite3
import os
from datetime import datetime
from functools import wraps

# ============================================================
# CONFIGURAÇÕES
# ============================================================

app = Flask(__name__)

# Chave usada para a sessão do administrador
app.secret_key = "frutafresca_chave_secreta_2026"

# Senha do administrador
SENHA_ADMIN = "fruta123"

# Local fixo para retirada
LOCAL_RETIRADA = "Av. Amazonas, 1815 - Universitário, Lajeado - RS, 95914-106"

# Caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
BANCO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco.db")


# ============================================================
# BANCO DE DADOS
# ============================================================

def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    return conexao


def adicionar_coluna_se_nao_existir(tabela, coluna, tipo):

    conexao = conectar()

    colunas = conexao.execute(
        f"PRAGMA table_info({tabela})"
    ).fetchall()

    nomes = [coluna_db["name"] for coluna_db in colunas]

    if coluna not in nomes:
        conexao.execute(
            f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}"
        )

    conexao.commit()
    conexao.close()


def criar_banco():

    conexao = conectar()

    # ========================================================
    # PRODUTOS
    # ========================================================

    conexao.execute("""
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
    """)

    # ========================================================
    # PEDIDOS
    # ========================================================

    conexao.execute("""
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
    """)

    # ========================================================
    # ITENS DOS PEDIDOS
    # ========================================================

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade_kg REAL NOT NULL,
            preco_kg REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)

    conexao.commit()
    conexao.close()

    # ========================================================
    # GARANTE QUE BANCOS ANTIGOS TENHAM AS COLUNAS
    # ========================================================

    colunas_pedidos = [
        ("nome_cliente", "TEXT"),
        ("telefone", "TEXT"),
        ("forma_entrega", "TEXT"),
        ("local_retirada", "TEXT"),
        ("observacao", "TEXT"),
        ("total", "REAL"),
        ("data_pedido", "TEXT")
    ]

    for coluna, tipo in colunas_pedidos:
        adicionar_coluna_se_nao_existir(
            "pedidos",
            coluna,
            tipo
        )

    # Preenche a data dos pedidos antigos que estiverem sem data
    conexao = conectar()

    conexao.execute("""
        UPDATE pedidos
        SET data_pedido = ?
        WHERE data_pedido IS NULL
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    conexao.commit()
    conexao.close()


# ============================================================
# PROTEÇÃO DO ADMINISTRADOR
# ============================================================

def somente_admin(funcao):

    @wraps(funcao)
    def verificar_admin(*args, **kwargs):

        if not session.get("admin_logado"):
            return redirect("/admin")

        return funcao(*args, **kwargs)

    return verificar_admin


# ============================================================
# INICIALIZAÇÃO
# ============================================================

criar_banco()


# ============================================================
# ABRIR SITE
# ============================================================

@app.route("/")
def inicio():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# ARQUIVOS DO FRONTEND
# ============================================================

@app.route("/<path:arquivo>")
def arquivos_frontend(arquivo):

    caminho = os.path.join(
        FRONTEND_DIR,
        arquivo
    )

    if os.path.isfile(caminho):

        return send_from_directory(
            FRONTEND_DIR,
            arquivo
        )

    return "Arquivo não encontrado", 404


# ============================================================
# LISTAR PRODUTOS
# ============================================================

@app.route("/produtos")
def produtos():

    conexao = conectar()

    lista_produtos = conexao.execute("""
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
    """).fetchall()

    conexao.close()

    return jsonify([
        dict(produto)
        for produto in lista_produtos
    ])


# ============================================================
# REGISTRAR PEDIDO
# ============================================================

@app.route("/pedidos", methods=["POST"])
def criar_pedido():

    try:

        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": "Nenhum dado foi enviado."
            }), 400

        nome_cliente = str(
            dados.get("nome_cliente", "")
        ).strip()

        telefone = str(
            dados.get("telefone", "")
        ).strip()

        observacao = str(
            dados.get("observacao", "")
        ).strip()

        itens = dados.get("itens", [])

        if not nome_cliente:

            return jsonify({
                "erro": "Informe o nome do cliente."
            }), 400

        if not itens:

            return jsonify({
                "erro": "O pedido não possui produtos."
            }), 400

        conexao = conectar()

        total = 0
        itens_processados = []

        # ====================================================
        # CALCULAR PEDIDO
        # ====================================================

        for item in itens:

            produto_id = int(
                item.get("produto_id")
            )

            quantidade = float(
                item.get("quantidade_kg", 0)
            )

            preco_kg = float(
                item.get("preco_kg", 0)
            )

            if quantidade <= 0:

                conexao.close()

                return jsonify({
                    "erro": "A quantidade deve ser maior que zero."
                }), 400

            subtotal = quantidade * preco_kg

            total += subtotal

            itens_processados.append({
                "produto_id": produto_id,
                "quantidade_kg": quantidade,
                "preco_kg": preco_kg,
                "subtotal": subtotal
            })

        # ====================================================
        # SALVAR PEDIDO
        # ====================================================

        data_pedido = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor = conexao.execute("""
            INSERT INTO pedidos (
                nome_cliente,
                telefone,
                forma_entrega,
                local_retirada,
                observacao,
                total,
                data_pedido
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            nome_cliente,
            telefone,
            "Retirada",
            LOCAL_RETIRADA,
            observacao,
            total,
            data_pedido
        ))

        pedido_id = cursor.lastrowid

        # ====================================================
        # SALVAR ITENS
        # ====================================================

        for item in itens_processados:

            conexao.execute("""
                INSERT INTO itens_pedido (
                    pedido_id,
                    produto_id,
                    quantidade_kg,
                    preco_kg,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item["produto_id"],
                item["quantidade_kg"],
                item["preco_kg"],
                item["subtotal"]
            ))

        conexao.commit()
        conexao.close()

        return jsonify({
            "sucesso": True,
            "pedido_id": pedido_id,
            "total": total,
            "local_retirada": LOCAL_RETIRADA
        })

    except Exception as erro:

        print("ERRO AO REGISTRAR PEDIDO:")
        print(erro)

        return jsonify({
            "erro": "Não foi possível registrar o pedido.",
            "detalhes": str(erro)
        }), 500


# ============================================================
# LOGIN DO ADMINISTRADOR
# ============================================================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        senha = request.form.get("senha", "")

        if senha == SENHA_ADMIN:

            session["admin_logado"] = True

            return redirect("/relatorio/mensal")

        return """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Acesso negado</title>

            <style>

                body {
                    font-family: Arial, sans-serif;
                    background: #f2f7f1;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }

                .caixa {
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    width: 350px;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.12);
                }

                h1 {
                    color: #285c2d;
                }

                .erro {
                    color: #c62828;
                    margin-bottom: 20px;
                }

                a {
                    color: #285c2d;
                }

            </style>

        </head>

        <body>

            <div class="caixa">

                <h1>FRUTAFRESCA</h1>

                <p class="erro">
                    Senha incorreta.
                </p>

                <a href="/admin">
                    Tentar novamente
                </a>

            </div>

        </body>
        </html>
        """

    return """
    <!DOCTYPE html>
    <html lang="pt-BR">

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Área Administrativa</title>

        <style>

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f2f7f1;
                min-height: 100vh;

                display: flex;
                align-items: center;
                justify-content: center;
            }

            .login {
                width: 400px;
                max-width: 90%;
                background: white;
                padding: 40px;
                border-radius: 24px;

                box-shadow:
                    0 15px 40px rgba(0,0,0,0.12);
            }

            h1 {
                color: #285c2d;
                text-align: center;
                margin-bottom: 10px;
            }

            p {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }

            label {
                display: block;
                font-weight: bold;
                margin-bottom: 8px;
            }

            input {
                width: 100%;
                padding: 14px;
                border: 1px solid #ccc;
                border-radius: 10px;
                font-size: 16px;
                margin-bottom: 20px;
            }

            button {
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 10px;

                background: #285c2d;
                color: white;

                font-size: 16px;
                font-weight: bold;

                cursor: pointer;
            }

            button:hover {
                background: #1e4723;
            }

        </style>

    </head>

    <body>

        <div class="login">

            <h1>FRUTAFRESCA</h1>

            <p>
                Área exclusiva do administrador
            </p>

            <form method="POST">

                <label>
                    Senha
                </label>

                <input
                    type="password"
                    name="senha"
                    placeholder="Digite a senha"
                    required
                >

                <button type="submit">
                    Entrar
                </button>

            </form>

        </div>

    </body>

    </html>
    """


# ============================================================
# RELATÓRIO MENSAL
# ============================================================

@app.route("/relatorio/mensal")
@somente_admin
def relatorio_mensal():

    conexao = conectar()

    mes_atual = datetime.now().strftime("%Y-%m")

    # ========================================================
    # TOTAL DE PEDIDOS
    # ========================================================

    resultado = conexao.execute("""
        SELECT COUNT(*) AS quantidade
        FROM pedidos
        WHERE substr(data_pedido, 1, 7) = ?
    """, (
        mes_atual,
    )).fetchone()

    total_pedidos = resultado["quantidade"]


    # ========================================================
    # FATURAMENTO
    # ========================================================

    resultado = conexao.execute("""
        SELECT COALESCE(SUM(total), 0) AS faturamento
        FROM pedidos
        WHERE substr(data_pedido, 1, 7) = ?
    """, (
        mes_atual,
    )).fetchone()

    faturamento = resultado["faturamento"]


    # ========================================================
    # KG VENDIDOS
    # ========================================================

    resultado = conexao.execute("""
        SELECT COALESCE(SUM(ip.quantidade_kg), 0) AS kg
        FROM itens_pedido ip
        INNER JOIN pedidos p
            ON p.id = ip.pedido_id
        WHERE substr(p.data_pedido, 1, 7) = ?
    """, (
        mes_atual,
    )).fetchone()

    kg_vendidos = resultado["kg"]


    # ========================================================
    # PRODUTOS MAIS VENDIDOS
    # ========================================================

    produtos_vendidos = conexao.execute("""
        SELECT
            pr.nome,
            SUM(ip.quantidade_kg) AS quantidade_kg,
            SUM(ip.subtotal) AS valor
        FROM itens_pedido ip
        INNER JOIN pedidos p
            ON p.id = ip.pedido_id
        INNER JOIN produtos pr
            ON pr.id = ip.produto_id
        WHERE substr(p.data_pedido, 1, 7) = ?
        GROUP BY pr.id, pr.nome
        ORDER BY quantidade_kg DESC
    """, (
        mes_atual,
    )).fetchall()


    # ========================================================
    # ÚLTIMOS PEDIDOS
    # ========================================================

    pedidos = conexao.execute("""
        SELECT
            id,
            nome_cliente,
            telefone,
            total,
            observacao,
            data_pedido
        FROM pedidos
        WHERE substr(data_pedido, 1, 7) = ?
        ORDER BY id DESC
    """, (
        mes_atual,
    )).fetchall()

    conexao.close()


    # ========================================================
    # TABELA DE PRODUTOS
    # ========================================================

    tabela_produtos = ""

    for produto in produtos_vendidos:

        tabela_produtos += f"""
        <tr>

            <td>
                {produto["nome"]}
            </td>

            <td>
                {float(produto["quantidade_kg"]):.2f} kg
            </td>

            <td>
                R$ {float(produto["valor"]):.2f}
            </td>

        </tr>
        """


    if not tabela_produtos:

        tabela_produtos = """
        <tr>
            <td colspan="3">
                Nenhum produto vendido neste mês.
            </td>
        </tr>
        """


    # ========================================================
    # TABELA DE PEDIDOS
    # ========================================================

    tabela_pedidos = ""

    for pedido in pedidos:

        observacao = pedido["observacao"] or ""

        tabela_pedidos += f"""
        <tr>

            <td>
                #{pedido["id"]}
            </td>

            <td>
                {pedido["nome_cliente"]}
            </td>

            <td>
                {pedido["telefone"] or "-"}
            </td>

            <td>
                R$ {float(pedido["total"]):.2f}
            </td>

            <td>
                {pedido["data_pedido"]}
            </td>

            <td>
                {observacao}
            </td>

        </tr>
        """


    if not tabela_pedidos:

        tabela_pedidos = """
        <tr>
            <td colspan="6">
                Nenhum pedido neste mês.
            </td>
        </tr>
        """


    # ========================================================
    # PÁGINA DO RELATÓRIO
    # ========================================================

    return f"""
    <!DOCTYPE html>

    <html lang="pt-BR">

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Relatório Mensal - Fruta Fresca</title>

        <style>

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f3f7f1;
                color: #243424;
            }}

            header {{
                background: #285c2d;
                color: white;
                padding: 25px 6%;

                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 20px;
            }}

            header h1 {{
                margin: 0;
                font-size: 28px;
            }}

            header a {{
                color: white;
                text-decoration: none;
                background: #e97820;
                padding: 10px 18px;
                border-radius: 10px;
            }}

            main {{
                width: 90%;
                max-width: 1200px;
                margin: 40px auto;
            }}

            .titulo {{
                margin-bottom: 30px;
            }}

            .titulo h2 {{
                margin: 0 0 8px;
                color: #285c2d;
            }}

            .titulo p {{
                color: #666;
            }}

            .cards {{
                display: grid;
                grid-template-columns:
                    repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 35px;
            }}

            .card {{
                background: white;
                padding: 25px;
                border-radius: 18px;

                box-shadow:
                    0 5px 20px rgba(0,0,0,0.07);
            }}

            .card h3 {{
                margin: 0 0 10px;
                color: #777;
                font-size: 15px;
            }}

            .numero {{
                font-size: 32px;
                font-weight: bold;
                color: #285c2d;
            }}

            .secao {{
                background: white;
                padding: 25px;
                border-radius: 18px;
                margin-bottom: 25px;

                box-shadow:
                    0 5px 20px rgba(0,0,0,0.07);
            }}

            .secao h2 {{
                color: #285c2d;
                margin-top: 0;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background: #285c2d;
                color: white;
                text-align: left;
            }}

            th, td {{
                padding: 13px;
                border-bottom: 1px solid #ddd;
            }}

            tr:hover {{
                background: #f7faf6;
            }}

            .seguro {{
                padding: 15px;
                background: #e8f4e6;
                border-left: 5px solid #285c2d;
                border-radius: 8px;
                margin-bottom: 25px;
            }}

            @media (max-width: 800px) {{

                .cards {{
                    grid-template-columns: 1fr;
                }}

                table {{
                    display: block;
                    overflow-x: auto;
                }}

                header {{
                    flex-direction: column;
                    align-items: flex-start;
                }}

            }}

        </style>

    </head>

    <body>

        <header>

            <h1>
                FRUTAFRESCA
            </h1>

            <a href="/admin/logout">
                Sair
            </a>

        </header>

        <main>

            <div class="titulo">

                <h2>
                    Relatório mensal
                </h2>

                <p>
                    Dados referentes ao mês atual:
                    {datetime.now().strftime("%m/%Y")}
                </p>

            </div>


            <div class="seguro">

                Área exclusiva do administrador.
                Os clientes não possuem acesso a este relatório.

            </div>


            <div class="cards">

                <div class="card">

                    <h3>
                        Pedidos realizados
                    </h3>

                    <div class="numero">
                        {total_pedidos}
                    </div>

                </div>


                <div class="card">

                    <h3>
                        Faturamento
                    </h3>

                    <div class="numero">
                        R$ {float(faturamento):.2f}
                    </div>

                </div>


                <div class="card">

                    <h3>
                        Frutas vendidas
                    </h3>

                    <div class="numero">
                        {float(kg_vendidos):.2f} kg
                    </div>

                </div>

            </div>


            <div class="secao">

                <h2>
                    Produtos vendidos
                </h2>

                <table>

                    <thead>

                        <tr>
                            <th>Produto</th>
                            <th>Quantidade</th>
                            <th>Valor</th>
                        </tr>

                    </thead>

                    <tbody>

                        {tabela_produtos}

                    </tbody>

                </table>

            </div>


            <div class="secao">

                <h2>
                    Pedidos do mês
                </h2>

                <table>

                    <thead>

                        <tr>
                            <th>Pedido</th>
                            <th>Cliente</th>
                            <th>Telefone</th>
                            <th>Total</th>
                            <th>Data</th>
                            <th>Observação</th>
                        </tr>

                    </thead>

                    <tbody>

                        {tabela_pedidos}

                    </tbody>

                </table>

            </div>

        </main>

    </body>

    </html>
    """


# ============================================================
# SAIR DO ADMIN
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logado", None)

    return redirect("/admin")


# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    print("=" * 45)
    print("FRUTAFRESCA")
    print("=" * 45)
    print("Banco de pedidos pronto!")
    print("Site: http://127.0.0.1:5000")
    print("Admin: http://127.0.0.1:5000/admin")
    print("Relatório: http://127.0.0.1:5000/relatorio/mensal")
    print("=" * 45)

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )