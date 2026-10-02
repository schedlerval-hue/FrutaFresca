let carrinho = [];

const API_URL = "http://127.0.0.1:5000";
const WHATSAPP = "5551980700507";

const LOCAL_RETIRADA =
    "Av. Amazonas, 1815 - Universitário, Lajeado - RS, 95914-106";


// =====================================================
// ADICIONAR PRODUTO
// =====================================================

function adicionarProduto(id, nome, preco, campoQuantidade) {

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

    const produtoExistente = carrinho.find(
        produto => produto.id === id
    );

    if (produtoExistente) {

        produtoExistente.quantidade += quantidade;

    } else {

        carrinho.push({
            id: id,
            nome: nome,
            preco: preco,
            quantidade: quantidade
        });

    }

    campo.value = "";

    atualizarCarrinho();

    document.getElementById("carrinho").scrollIntoView({
        behavior: "smooth"
    });
}


// =====================================================
// ATUALIZAR CARRINHO
// =====================================================

function atualizarCarrinho() {

    const lista = document.getElementById("lista-carrinho");
    const quantidadeCarrinho =
        document.getElementById("quantidade-carrinho");
    const totalCarrinho =
        document.getElementById("total-carrinho");

    if (!lista) return;

    if (carrinho.length === 0) {

        lista.innerHTML = `
            <p class="carrinho-vazio">
                Seu carrinho está vazio.
            </p>
        `;

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

        const item = document.createElement("div");

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


// =====================================================
// REMOVER PRODUTO
// =====================================================

function removerProduto(indice) {

    carrinho.splice(indice, 1);

    atualizarCarrinho();
}


// =====================================================
// DINHEIRO
// =====================================================

function formatarReal(valor) {

    return valor.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}


// =====================================================
// ABRIR FORMULÁRIO
// =====================================================

function finalizarPedido() {

    if (carrinho.length === 0) {

        alert("Adicione pelo menos uma fruta ao pedido.");

        return;
    }

    const modal =
        document.getElementById("modal-pedido");

    if (!modal) {

        alert("Formulário de pedido não encontrado.");

        return;
    }

    modal.classList.add("ativo");
}


// =====================================================
// FECHAR FORMULÁRIO
// =====================================================

function fecharModal() {

    const modal =
        document.getElementById("modal-pedido");

    if (modal) {
        modal.classList.remove("ativo");
    }
}


// =====================================================
// ENVIAR PEDIDO
// =====================================================

async function enviarPedidoWhatsApp() {

    const nome =
        document.getElementById("cliente-nome").value.trim();

    const telefone =
        document.getElementById("cliente-telefone").value.trim();

    const observacao =
        document.getElementById("cliente-observacao").value.trim();


    // -------------------------------------------------
    // VALIDAÇÕES
    // -------------------------------------------------

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


    // -------------------------------------------------
    // CALCULAR TOTAL
    // -------------------------------------------------

    let total = 0;

    carrinho.forEach(produto => {

        total +=
            produto.preco *
            produto.quantidade;

    });


    // -------------------------------------------------
    // DADOS DO PEDIDO
    // -------------------------------------------------

    const dadosPedido = {

        nome_cliente: nome,

        telefone: telefone,

        forma_entrega: "Retirada",

        local_retirada: LOCAL_RETIRADA,

        observacao: observacao,

        total: total,

        itens: carrinho.map(produto => ({

            produto_id: produto.id,

            quantidade_kg: produto.quantidade,

            preco_kg: produto.preco

        }))

    };


    // -------------------------------------------------
    // TENTAR SALVAR NA API
    // -------------------------------------------------

    let numeroPedido = null;

    try {

        const resposta = await fetch(
            `${API_URL}/pedidos`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(dadosPedido)
            }
        );


        if (resposta.ok) {

            const resultado =
                await resposta.json();

            numeroPedido =
                resultado.pedido_id || null;

        } else {

            console.warn(
                "A API respondeu com erro:",
                resposta.status
            );

        }

    } catch (erro) {

        console.warn(
            "Não foi possível conectar à API:",
            erro
        );

    }


    // -------------------------------------------------
    // MONTAR MENSAGEM DO WHATSAPP
    // -------------------------------------------------

    let mensagem =
        "NOVO PEDIDO - FRUTA FRESCA\n\n";


    if (numeroPedido) {

        mensagem +=
            `Pedido nº: ${numeroPedido}\n\n`;

    }


    mensagem +=
        "DADOS DO CLIENTE\n";

    mensagem +=
        `Nome: ${nome}\n`;

    mensagem +=
        `Telefone: ${telefone}\n\n`;


    mensagem +=
        "FORMA DE RETIRADA\n";

    mensagem +=
        "Retirada no local\n";

    mensagem +=
        `Local: ${LOCAL_RETIRADA}\n\n`;


    mensagem +=
        "PRODUTOS\n";


    carrinho.forEach(produto => {

        const subtotal =
            produto.preco *
            produto.quantidade;


        mensagem +=
            `${produto.nome}\n`;

        mensagem +=
            `Quantidade: ${produto.quantidade.toFixed(2)} kg\n`;

        mensagem +=
            `Preço: ${formatarReal(produto.preco)}/kg\n`;

        mensagem +=
            `Subtotal: ${formatarReal(subtotal)}\n\n`;

    });


    mensagem +=
        `TOTAL: ${formatarReal(total)}\n`;


    if (observacao) {

        mensagem +=
            `\nObservação: ${observacao}\n`;

    }


    // -------------------------------------------------
    // FECHAR MODAL
    // -------------------------------------------------

    fecharModal();


    // -------------------------------------------------
    // ABRIR WHATSAPP
    // -------------------------------------------------

    const urlWhatsApp =
        "https://wa.me/" +
        WHATSAPP +
        "?text=" +
        encodeURIComponent(mensagem);


    window.location.href = urlWhatsApp;
}


// =====================================================
// INICIAR
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        atualizarCarrinho();

    }
);