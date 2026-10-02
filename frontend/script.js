let carrinho = [];

const API_URL = "http://127.0.0.1:5000";

const LOCAL_RETIRADA =
    "Av. Amazonas, 1815 - Universitário, Lajeado - RS, 95914-106";

let produtosEstoque = [];

// ===============================
// CARREGAR PRODUTOS E ESTOQUE
// ===============================

async function carregarEstoque() {
    try {
        const resposta = await fetch(`${API_URL}/produtos`);

        if (!resposta.ok) {
            throw new Error("Erro ao buscar produtos.");
        }

        produtosEstoque = await resposta.json();

        mostrarEstoques();

    } catch (erro) {
        console.error("Erro ao carregar estoque:", erro);
        alert("Não foi possível carregar o estoque.");
    }
}


// ===============================
// MOSTRAR ESTOQUE NA TELA
// ===============================

function mostrarEstoques() {

    produtosEstoque.forEach(produto => {

        let campoQuantidade = "";

        if (produto.nome === "Morango") {
            campoQuantidade = "quantidade-morango";
        }

        if (produto.nome === "Uva") {
            campoQuantidade = "quantidade-uva";
        }

        if (produto.nome === "Laranja") {
            campoQuantidade = "quantidade-laranja";
        }

        if (!campoQuantidade) return;

        const campo = document.getElementById(campoQuantidade);

        if (!campo) return;

        let estoqueElemento = document.getElementById(
            `estoque-${produto.id}`
        );

        if (!estoqueElemento) {

            estoqueElemento = document.createElement("p");

            estoqueElemento.id = `estoque-${produto.id}`;

            estoqueElemento.style.marginTop = "5px";

            campo.parentElement.appendChild(estoqueElemento);
        }

        estoqueElemento.textContent =
            `Estoque disponível: ${produto.estoque.toFixed(2)} kg`;
    });
}


// ===============================
// ADICIONAR PRODUTO AO CARRINHO
// ===============================

async function adicionarProduto(
    id,
    nome,
    preco,
    campoQuantidade
) {

    if (produtosEstoque.length === 0) {
        await carregarEstoque();
    }

    const campo = document.getElementById(campoQuantidade);

    if (!campo) {
        alert("Campo de quantidade não encontrado.");
        return;
    }

    const quantidade = parseFloat(campo.value);

    if (isNaN(quantidade) || quantidade <= 0) {
        alert("Informe uma quantidade válida em kg.");
        return;
    }

    const produtoEstoque = produtosEstoque.find(
        produto => Number(produto.id) === Number(id)
    );

    if (!produtoEstoque) {
        alert("Produto não encontrado no estoque.");
        return;
    }

    const produtoExistente = carrinho.find(
        produto => produto.id === id
    );

    const quantidadeNoCarrinho = produtoExistente
        ? produtoExistente.quantidade
        : 0;

    const novaQuantidade =
        quantidadeNoCarrinho + quantidade;

    if (novaQuantidade > produtoEstoque.estoque) {

        alert(
            `Não há estoque suficiente de ${nome}.\n\n` +
            `Estoque disponível: ${produtoEstoque.estoque.toFixed(2)} kg\n` +
            `Quantidade solicitada: ${novaQuantidade.toFixed(2)} kg`
        );

        return;
    }

    if (produtoExistente) {

        produtoExistente.quantidade += quantidade;

    } else {

        carrinho.push({
            id: produtoEstoque.id,
            nome: produtoEstoque.nome,
            preco: produtoEstoque.preco,
            quantidade: quantidade
        });
    }

    campo.value = "";

    atualizarCarrinho();

    document
        .getElementById("carrinho")
        .scrollIntoView({
            behavior: "smooth"
        });
}


// ===============================
// ATUALIZAR CARRINHO
// ===============================

function atualizarCarrinho() {

    const lista =
        document.getElementById("lista-carrinho");

    const quantidadeCarrinho =
        document.getElementById("quantidade-carrinho");

    const totalCarrinho =
        document.getElementById("total-carrinho");

    if (!lista) return;

    if (carrinho.length === 0) {

        lista.innerHTML =
            `<p class="carrinho-vazio">
                Seu carrinho está vazio.
            </p>`;

        if (quantidadeCarrinho) {
            quantidadeCarrinho.textContent = "0 kg";
        }

        if (totalCarrinho) {
            totalCarrinho.textContent = "R$ 0,00";
        }

        return;
    }

    lista.innerHTML = "";

    let total = 0;
    let quantidadeTotal = 0;

    carrinho.forEach((produto, indice) => {

        const subtotal =
            produto.preco * produto.quantidade;

        total += subtotal;

        quantidadeTotal += produto.quantidade;

        const item =
            document.createElement("div");

        item.className = "item-carrinho";

        item.innerHTML = `
            <div class="item-info">
                <strong>${produto.nome}</strong>

                <p>
                    ${produto.quantidade.toFixed(2)} kg ×
                    ${formatarReal(produto.preco)}/kg
                </p>
            </div>

            <div class="subtotal">
                ${formatarReal(subtotal)}
            </div>

            <button
                class="remover"
                onclick="removerProduto(${indice})">
                Remover
            </button>
        `;

        lista.appendChild(item);
    });

    if (quantidadeCarrinho) {
        quantidadeCarrinho.textContent =
            quantidadeTotal.toFixed(2) + " kg";
    }

    if (totalCarrinho) {
        totalCarrinho.textContent =
            formatarReal(total);
    }
}


// ===============================
// REMOVER PRODUTO
// ===============================

function removerProduto(indice) {

    carrinho.splice(indice, 1);

    atualizarCarrinho();
}


// ===============================
// FORMATAR DINHEIRO
// ===============================

function formatarReal(valor) {

    return valor.toLocaleString(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL"
        }
    );
}


// ===============================
// ABRIR MODAL
// ===============================

function finalizarPedido() {

    if (carrinho.length === 0) {

        alert(
            "Adicione pelo menos uma fruta ao pedido."
        );

        return;
    }

    const modal =
        document.getElementById("modal-pedido");

    if (!modal) {

        alert(
            "Formulário de pedido não encontrado."
        );

        return;
    }

    modal.classList.add("ativo");
}


// ===============================
// FECHAR MODAL
// ===============================

function fecharModal() {

    const modal =
        document.getElementById("modal-pedido");

    if (modal) {
        modal.classList.remove("ativo");
    }
}


// ===============================
// FINALIZAR PEDIDO
// ===============================

async function enviarPedidoWhatsApp() {

    const nome =
        document
            .getElementById("cliente-nome")
            .value
            .trim();

    const telefone =
        document
            .getElementById("cliente-telefone")
            .value
            .trim();

    const observacao =
        document
            .getElementById("cliente-observacao")
            .value
            .trim();

    if (!nome) {

        alert("Informe seu nome.");

        return;
    }

    if (!telefone) {

        alert("Informe seu telefone.");

        return;
    }

    if (carrinho.length === 0) {

        alert("Adicione pelo menos uma fruta.");

        return;
    }

    let total = 0;

    carrinho.forEach(produto => {

        total +=
            produto.preco *
            produto.quantidade;
    });


    const dadosPedido = {

        nome_cliente: nome,

        telefone: telefone,

        forma_entrega: "Retirada",

        local_retirada: LOCAL_RETIRADA,

        observacao: observacao,

        total: total,

        itens: carrinho.map(produto => ({

            produto_id: produto.id,

            quantidade_kg:
                produto.quantidade,

            preco_kg:
                produto.preco

        }))
    };


    try {

        const resposta = await fetch(
            `${API_URL}/pedidos`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(dadosPedido)
            }
        );


        const resultado =
            await resposta.json();


        if (!resposta.ok) {

            alert(
                resultado.erro ||
                "Não foi possível finalizar o pedido."
            );

            return;
        }


        fecharModal();


        alert(
            `Pedido realizado com sucesso!\n\n` +
            `Número do pedido: ${resultado.pedido_id}\n` +
            `Total: ${formatarReal(resultado.total)}`
        );


        carrinho = [];

        atualizarCarrinho();

        await carregarEstoque();


    } catch (erro) {

        console.error(erro);

        alert(
            "Não foi possível conectar ao sistema de pedidos."
        );
    }
}


// ===============================
// INICIAR SITE
// ===============================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        atualizarCarrinho();

        carregarEstoque();

    }
);