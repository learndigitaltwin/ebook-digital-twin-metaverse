// =============================================================================
//  Dashboard Web da Esteira - logica da pagina (frontend)
// =============================================================================
//
//  Este arquivo:
//    1. Descreve a linha de producao (CONFIG) de forma simples de editar.
//    2. Monta a cena visual da esteira a partir dessa descricao.
//    3. Carrega o historico inicial (/api/estado).
//    4. Ouve os eventos em tempo real (/eventos via SSE) e atualiza a tela.
//
//  Como os tres tutoriais (Unity, Unreal e Isaac Sim) usam a MESMA esteira,
//  basta enviar eventos no mesmo formato para reaproveitar este dashboard.
//  Para adaptar a outra linha, edite apenas o objeto CONFIG abaixo.
// =============================================================================


// -----------------------------------------------------------------------------
//  1) CONFIGURACAO DA LINHA DE PRODUCAO
// -----------------------------------------------------------------------------
//  As estacoes estao na ordem fisica da esteira (da esquerda para a direita).
//  "posicao" e a posicao horizontal na cena, em porcentagem (0 = inicio).
//  "cor" e a cor que a caixa recebe ao ser pintada naquela estacao.
const CONFIG = {
    estacoes: [
        {
            id: "entrada", rotulo: "Entrada", posicao: 7,
            sensor: "Sensor_1", cabecote: null,
            estagio: "Entrada do processo", cor: null
        },
        {
            id: "pontoA", rotulo: "Ponto A", posicao: 33,
            sensor: "Sensor_2", cabecote: "Cabecote_1",
            estagio: "Pintura de base", cor: "#9aa6b2"
        },
        {
            id: "pontoB", rotulo: "Ponto B", posicao: 56,
            sensor: "Sensor_3", cabecote: "Cabecote_2",
            estagio: "Tinta de acabamento", cor: "#2f6fb0"
        },
        {
            id: "pontoC", rotulo: "Ponto C", posicao: 79,
            sensor: "Sensor_4", cabecote: "Cabecote_3",
            estagio: "Verniz protetor", cor: "#1c497a", verniz: true
        },
        {
            id: "expedicao", rotulo: "Expedição", posicao: 95,
            sensor: null, cabecote: null,
            estagio: "Saída para expedição", cor: null
        }
    ]
};


// -----------------------------------------------------------------------------
//  2) ESTADO INTERNO (montado a partir do CONFIG)
// -----------------------------------------------------------------------------

// Mapas usados para contar passagens e montar os cartoes.
// Ex.: sensores["Sensor_2"] = { nome, estagio, total, ultimaCaixa, ... }
const sensores = {};
const cabecotes = {};

CONFIG.estacoes.forEach((estacao) => {
    if (estacao.sensor) {
        sensores[estacao.sensor] = criarItem(estacao.rotulo, estacao.estagio);
    }
    if (estacao.cabecote) {
        cabecotes[estacao.cabecote] = criarItem(estacao.rotulo, estacao.estagio);
    }
});

function criarItem(nome, estagio) {
    return { nome, estagio, total: 0, ultimaCaixa: "-", ultimoHorario: "-" };
}

// Lista com todos os eventos ja recebidos.
let eventos = [];

// Caixas que estao na cena AGORA. Cada caixa vira um elemento proprio na tela,
// indexado pelo seu nome (ex.: "Caixa 1"). Assim varias caixas aparecem ao
// mesmo tempo na esteira, cada uma na sua posicao.
//   caixasNaCena["Caixa 1"] = { elemento, saindo }
const caixasNaCena = {};


// -----------------------------------------------------------------------------
//  3) REFERENCIAS AOS ELEMENTOS DA PAGINA
// -----------------------------------------------------------------------------

const totalEventos = document.getElementById("totalEventos");
const ultimaCaixa = document.getElementById("ultimaCaixa");
const ultimoHorario = document.getElementById("ultimoHorario");
const fonteDados = document.getElementById("fonteDados");
const statusConexao = document.getElementById("statusConexao");
const cardsSensores = document.getElementById("cardsSensores");
const cardsCabecotes = document.getElementById("cardsCabecotes");
const historico = document.getElementById("historico");
const cenaEsteira = document.getElementById("cenaEsteira");


// -----------------------------------------------------------------------------
//  4) INICIALIZACAO
// -----------------------------------------------------------------------------

montarCena();
iniciarDashboard();

async function iniciarDashboard() {
    await carregarEstadoInicial();
    conectarEventos();
}


// -----------------------------------------------------------------------------
//  5) MONTAGEM DA CENA VISUAL DA ESTEIRA
// -----------------------------------------------------------------------------
//  Desenha o trilho, as estacoes (sensor em vermelho, cabecote em amarelo)
//  e a caixa que se move ao longo da esteira.
function montarCena() {
    let html = '<div class="trilho"></div>';

    // Cria cada estacao na sua posicao horizontal.
    CONFIG.estacoes.forEach((estacao) => {
        const cabecote = estacao.cabecote
            ? `<div class="cabecote" id="cab-${estacao.cabecote}" title="${estacao.cabecote}">
                   <span class="bico"></span>
               </div>`
            : "";

        const sensor = estacao.sensor
            ? `<div class="sensor" id="sen-${estacao.sensor}" title="${estacao.sensor}"></div>`
            : "";

        html += `
            <div class="estacao" style="left:${estacao.posicao}%">
                ${cabecote}
                ${sensor}
                <div class="rotulo-estacao">
                    <strong>${estacao.rotulo}</strong>
                    <span>${estacao.estagio}</span>
                </div>
            </div>`;
    });

    // As caixas NAO sao criadas aqui: cada caixa que entra na esteira ganha
    // o seu proprio elemento, criado dinamicamente quando o evento chega.
    cenaEsteira.innerHTML = html;
}


// -----------------------------------------------------------------------------
//  6) CARGA INICIAL E CONEXAO EM TEMPO REAL
// -----------------------------------------------------------------------------

async function carregarEstadoInicial() {
    try {
        const resposta = await fetch("/api/estado");
        const dados = await resposta.json();
        eventos = dados.eventos || [];
        recalcularEstado();   // reconstroi os contadores a partir do historico
        atualizarTela();
    } catch {
        statusConexao.textContent = "Servidor indisponível";
        statusConexao.className = "status-conexao offline";
    }
}

function conectarEventos() {
    // EventSource e a forma nativa do navegador de receber dados via SSE.
    const fonte = new EventSource("/eventos");

    fonte.onopen = function () {
        statusConexao.textContent = "Conectado";
        statusConexao.className = "status-conexao online";
    };

    fonte.onmessage = function (mensagem) {
        const evento = JSON.parse(mensagem.data);

        // Evento especial enviado por /api/limpar: zera tudo.
        if (evento.tipo === "_limpar") {
            limparTudo();
            return;
        }

        eventos.push(evento);
        aplicarEvento(evento);
        animarCena(evento);
        atualizarTela();
    };

    fonte.onerror = function () {
        statusConexao.textContent = "Reconectando...";
        statusConexao.className = "status-conexao offline";
    };
}


// -----------------------------------------------------------------------------
//  7) PROCESSAMENTO DOS EVENTOS (contadores)
// -----------------------------------------------------------------------------

function recalcularEstado() {
    limparContadores();
    eventos.forEach(aplicarEvento);
}

function limparContadores() {
    Object.values(sensores).forEach(zerarItem);
    Object.values(cabecotes).forEach(zerarItem);
}

function zerarItem(item) {
    item.total = 0;
    item.ultimaCaixa = "-";
    item.ultimoHorario = "-";
}

// Atualiza os contadores conforme o tipo do evento.
function aplicarEvento(evento) {
    if (evento.tipo === "sensor" && sensores[evento.origem]) {
        atualizarItem(sensores[evento.origem], evento);
    }
    if (evento.tipo === "cabecote" && cabecotes[evento.origem]) {
        atualizarItem(cabecotes[evento.origem], evento);
    }
}

function atualizarItem(item, evento) {
    item.total += 1;
    item.ultimaCaixa = evento.caixa || "-";
    item.ultimoHorario = evento.dataHora || "-";
}


// -----------------------------------------------------------------------------
//  8) ANIMACAO DA CENA
// -----------------------------------------------------------------------------
//  Cada caixa tem o seu proprio elemento. A cada evento: localizamos (ou
//  criamos) a caixa pelo nome, movemos para a estacao, acendemos o sensor
//  (vermelho) ou o cabecote (amarelo) e pintamos a caixa com a cor do estagio.

// Estacao final (expedicao) e ultima estacao que tem sensor/cabecote (Ponto C).
// Usadas para fazer a caixa "sair" da esteira depois do ultimo estagio.
const ESTACAO_FINAL = CONFIG.estacoes[CONFIG.estacoes.length - 1];
const ULTIMA_ESTACAO_PROCESSO = [...CONFIG.estacoes]
    .reverse()
    .find((e) => e.sensor || e.cabecote);

function animarCena(evento) {
    const estacao = encontrarEstacao(evento);
    if (!estacao) return;

    const nomeDaCaixa = evento.caixa || "Caixa";
    const caixa = obterOuCriarCaixa(nomeDaCaixa, estacao);

    // Move a caixa para a posicao da estacao (a animacao vem do CSS).
    caixa.elemento.style.left = estacao.posicao + "%";

    // Acende o indicador certo: sensor (vermelho) ou cabecote (amarelo).
    if (evento.tipo === "sensor" && estacao.sensor) {
        piscar(document.getElementById("sen-" + estacao.sensor));
    }
    if (evento.tipo === "cabecote" && estacao.cabecote) {
        piscar(document.getElementById("cab-" + estacao.cabecote));
        pintarCaixa(caixa.elemento, estacao); // a tinta e aplicada pelo cabecote
    }

    // Ao chegar na ultima estacao de processo (Ponto C), a caixa segue para a
    // expedicao e depois e removida da cena, liberando espaco para as proximas.
    if (estacao === ULTIMA_ESTACAO_PROCESSO) {
        agendarSaida(nomeDaCaixa);
    }
}

// Encontra a estacao a que o evento pertence (pelo sensor ou pelo cabecote).
function encontrarEstacao(evento) {
    return CONFIG.estacoes.find(
        (e) => e.sensor === evento.origem || e.cabecote === evento.origem
    );
}

// Devolve a caixa da cena com este nome. Se ainda nao existir, cria o elemento.
function obterOuCriarCaixa(nome, estacao) {
    if (caixasNaCena[nome]) {
        return caixasNaCena[nome];
    }

    const elemento = document.createElement("div");
    elemento.className = "caixa-movel";
    elemento.style.left = estacao.posicao + "%"; // nasce na posicao do 1o evento

    const rotulo = document.createElement("span");
    rotulo.textContent = nome;
    elemento.appendChild(rotulo);

    cenaEsteira.appendChild(elemento);

    caixasNaCena[nome] = { elemento, saindo: false };
    return caixasNaCena[nome];
}

// Pinta uma caixa com a cor do estagio (aplicado pelo cabecote).
function pintarCaixa(elemento, estacao) {
    if (!estacao.cor) return;
    elemento.style.background = estacao.cor;
    if (estacao.verniz) {
        elemento.classList.add("tem-verniz"); // brilho extra do verniz
    }
}

// Faz a caixa caminhar ate a expedicao e depois some da cena.
function agendarSaida(nome) {
    const caixa = caixasNaCena[nome];
    if (!caixa || caixa.saindo) return; // evita agendar duas vezes
    caixa.saindo = true;

    // 1) espera um instante parada no Ponto C, depois anda ate a expedicao
    setTimeout(() => {
        caixa.elemento.style.left = ESTACAO_FINAL.posicao + "%";

        // 2) terminado o trajeto, faz a caixa desaparecer suavemente
        setTimeout(() => {
            caixa.elemento.classList.add("oculta");

            // 3) por fim, remove o elemento e esquece a caixa
            setTimeout(() => {
                caixa.elemento.remove();
                delete caixasNaCena[nome];
            }, 400);
        }, 900);
    }, 1200);
}

// Acende um elemento por um instante (animacao de "pulso").
function piscar(elemento) {
    if (!elemento) return;
    elemento.classList.add("ativo");
    setTimeout(() => elemento.classList.remove("ativo"), 900);
}


// -----------------------------------------------------------------------------
//  9) ATUALIZACAO DA TELA (cartoes, resumo e historico)
// -----------------------------------------------------------------------------

function atualizarTela() {
    const ultimoEvento = eventos[eventos.length - 1];

    totalEventos.textContent = eventos.length;
    ultimaCaixa.textContent = ultimoEvento ? ultimoEvento.caixa || "-" : "-";
    ultimoHorario.textContent = ultimoEvento ? ultimoEvento.dataHora || "-" : "-";
    fonteDados.textContent = ultimoEvento ? ultimoEvento.fonte || "-" : "-";

    cardsSensores.innerHTML = criarCards(sensores, "sensor");
    cardsCabecotes.innerHTML = criarCards(cabecotes, "cabecote");
    historico.innerHTML = criarHistorico();
}

function criarCards(itens, tipo) {
    return Object.entries(itens).map(([origem, item]) => `
        <article class="card card-${tipo}">
            <strong>${item.nome}</strong>
            <span>${origem} - ${item.estagio}</span>
            <div class="linha-card">
                <span>Última Caixa: ${item.ultimaCaixa}</span>
                <b class="badge">${item.total}</b>
            </div>
            <span>Último Horário: ${item.ultimoHorario}</span>
        </article>
    `).join("");
}

function criarHistorico() {
    if (eventos.length === 0) {
        return '<p class="vazio">Nenhum evento recebido ainda.</p>';
    }

    // Mostra do mais recente para o mais antigo.
    return [...eventos].reverse().map((evento) => `
        <article class="item-historico tipo-${evento.tipo || "outro"}">
            <strong>${evento.mensagem || "Evento recebido"}</strong>
            <small>${evento.dataHora || "-"} | ${evento.origem || "-"} | ${evento.estagio || "-"}</small>
        </article>
    `).join("");
}

// Zera completamente a tela (usado pelo botao "limpar" no servidor).
function limparTudo() {
    eventos = [];
    limparContadores();

    // Remove da cena todas as caixas que estiverem na esteira.
    Object.keys(caixasNaCena).forEach((nome) => {
        caixasNaCena[nome].elemento.remove();
        delete caixasNaCena[nome];
    });

    atualizarTela();
}
