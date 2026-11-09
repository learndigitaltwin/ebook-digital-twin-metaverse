# =============================================================================
#  Dashboard Web da Esteira - Gemeo Digital (servidor FastAPI)
# =============================================================================
#
#  O QUE ESTE ARQUIVO FAZ
#  ----------------------
#  Este e um pequeno servidor web que:
#    1. Recebe eventos de QUALQUER fonte (Unity, Unreal, Isaac Sim, ou ate de
#       um teste manual) atraves de um POST HTTP em /api/eventos.
#    2. Guarda esses eventos em memoria (uma lista simples).
#    3. Reenvia cada evento, em tempo real, para a pagina do dashboard aberta
#       no navegador, usando SSE (Server-Sent Events).
#
#  Ele e "universal": nao conhece nem depende do Unity. Qualquer programa que
#  saiba enviar um JSON por HTTP consegue alimentar este dashboard.
#
# -----------------------------------------------------------------------------
#  COMO EXECUTAR
# -----------------------------------------------------------------------------
#
#  FORMA 1 (recomendada): dois cliques no arquivo  start_dashboard.bat
#     Ele cria o ambiente virtual, instala as dependencias, abre o navegador
#     e inicia o servidor automaticamente.
#
#  FORMA 2 (manual, caso o .bat nao funcione): abra o Prompt de Comando
#     (cmd) ou o PowerShell DENTRO da pasta DashboardWeb_Python e rode, na
#     ordem, os comandos abaixo:
#
#       1) Criar o ambiente virtual (so na primeira vez):
#            python -m venv .venv
#
#       2) Ativar o ambiente virtual:
#            - No Prompt de Comando (cmd):   .venv\Scripts\activate.bat
#            - No PowerShell:                .venv\Scripts\Activate.ps1
#
#       3) Instalar as dependencias (so na primeira vez):
#            python -m pip install -r requirements.txt
#
#       4) Iniciar o servidor:
#            python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 --timeout-graceful-shutdown 5
#
#     Depois, abra o navegador em:   http://localhost:8000
#
#  Observacao: se o comando "python" nao existir, tente trocar por "py".
#
#  Para parar o servidor, volte ao terminal e pressione  Ctrl + C.
#  A opcao --timeout-graceful-shutdown 5 faz o servidor desligar em ate 5s.
#  Sem ela, o dashboard mantem uma conexao aberta (SSE) e o Ctrl + C poderia
#  travar em "Waiting for connections to close" enquanto a pagina estiver aberta.
#
# =============================================================================

import asyncio
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles


# -----------------------------------------------------------------------------
#  Configuracao geral
# -----------------------------------------------------------------------------

app = FastAPI(title="Dashboard Web da Esteira")

# Libera o acesso de qualquer origem. Isso deixa o dashboard "universal":
# uma fonte rodando em outra porta/maquina (Unreal, Isaac Sim, etc.) tambem
# consegue enviar eventos sem ser bloqueada pelo navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pasta onde estao os arquivos da pagina (index.html, style.css, script.js).
PASTA_DO_DASHBOARD = Path(__file__).parent

# Quantos eventos manter em memoria (os mais antigos sao descartados).
LIMITE_DE_EVENTOS = 200


# -----------------------------------------------------------------------------
#  Estado em memoria (zera toda vez que o servidor reinicia)
# -----------------------------------------------------------------------------

# Lista com os eventos ja recebidos (o historico).
eventos: list[dict[str, Any]] = []

# Uma fila para cada navegador conectado. Quando um evento chega, ele e
# colocado em todas as filas, e cada navegador recebe sua copia.
clientes_conectados: list[asyncio.Queue] = []

# Numero sequencial dado a cada evento, util para o frontend identifica-los.
proximo_id = 1


# Disponibiliza a pasta "static" (css e js) na URL /static.
app.mount("/static", StaticFiles(directory=PASTA_DO_DASHBOARD / "static"), name="static")


# -----------------------------------------------------------------------------
#  Funcoes auxiliares
# -----------------------------------------------------------------------------

def normalizar_texto(valor: Any) -> str:
    """Coloca um texto em minusculas e remove acentos.

    Serve para comparar o campo "tipo" sem se preocupar com variacoes como
    "cabecote", "Cabecote" ou "cabeçote" (com cedilha). Todas viram "cabecote".
    """
    texto = str(valor or "").strip().lower()
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


def preparar_evento(evento_bruto: dict[str, Any]) -> dict[str, Any]:
    """Recebe o JSON cru enviado pela fonte e devolve um evento padronizado.

    Aqui garantimos que todo evento tenha os campos basicos preenchidos,
    independentemente de qual programa o enviou.
    """
    global proximo_id

    evento = dict(evento_bruto)  # copia para nao alterar o original

    # Identificador unico e crescente.
    evento["id"] = proximo_id
    proximo_id += 1

    # "tipo" padronizado (sensor / cabecote / ...), sem acento e em minusculo.
    evento["tipo"] = normalizar_texto(evento.get("tipo"))

    # Quem enviou o evento. Se a fonte nao informar, marcamos "desconhecida".
    # Isso ajuda quando o mesmo dashboard for usado por Unity, Unreal e Isaac.
    evento["fonte"] = str(evento.get("fonte") or "desconhecida")

    # Se a fonte nao mandou data/hora, preenchemos com a hora do servidor.
    if not evento.get("dataHora"):
        evento["dataHora"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return evento


# -----------------------------------------------------------------------------
#  Rotas (endpoints) do servidor
# -----------------------------------------------------------------------------

@app.get("/")
def abrir_dashboard():
    """Abre a pagina do dashboard (o arquivo index.html)."""
    return FileResponse(PASTA_DO_DASHBOARD / "static" / "index.html")


@app.get("/api/health")
def verificar():
    """Endpoint simples para testar se o servidor esta no ar.

    Abra http://localhost:8000/api/health no navegador: se aparecer um JSON,
    o servidor esta funcionando.
    """
    return {"ok": True, "totalEventos": len(eventos), "clientes": len(clientes_conectados)}


@app.get("/api/estado")
def obter_estado_atual():
    """Devolve todos os eventos guardados na memoria.

    O navegador chama esta rota assim que a pagina abre, para reconstruir o
    que ja aconteceu antes de comecar a ouvir os eventos em tempo real.
    """
    return {"eventos": eventos}


@app.post("/api/eventos")
async def receber_evento(evento_bruto: dict[str, Any]):
    """Recebe um evento (em JSON) de qualquer fonte e o distribui.

    Exemplo de JSON aceito:
        {
          "tipo": "sensor",
          "origem": "Sensor_2",
          "caixa": "Caixa 1",
          "estagio": "Ponto A - pintura de base",
          "mensagem": "Caixa 1 detectada no Ponto A",
          "fonte": "Unity"
        }
    """
    evento = preparar_evento(evento_bruto)

    # Guarda no historico e respeita o limite maximo de eventos.
    eventos.append(evento)
    if len(eventos) > LIMITE_DE_EVENTOS:
        eventos.pop(0)

    # Entrega o evento para todos os navegadores conectados.
    for fila_do_cliente in list(clientes_conectados):
        await fila_do_cliente.put(evento)

    return {"ok": True, "id": evento["id"]}


@app.post("/api/limpar")
async def limpar_eventos():
    """Apaga o historico em memoria. Util para recomecar um teste do zero."""
    eventos.clear()

    # Avisa os navegadores para tambem limparem a tela.
    for fila_do_cliente in list(clientes_conectados):
        await fila_do_cliente.put({"tipo": "_limpar"})

    return {"ok": True}


@app.get("/eventos")
async def ouvir_eventos():
    """Canal SSE: mantem a conexao aberta e envia cada novo evento ao navegador.

    O navegador usa "new EventSource('/eventos')" para se inscrever aqui.
    """
    fila_do_cliente: asyncio.Queue = asyncio.Queue()
    clientes_conectados.append(fila_do_cliente)

    async def gerar_fluxo():
        try:
            while True:
                try:
                    # Espera por um novo evento por ate 15 segundos.
                    evento = await asyncio.wait_for(fila_do_cliente.get(), timeout=15)
                    texto = json.dumps(evento, ensure_ascii=False)
                    yield f"data: {texto}\n\n"
                except asyncio.TimeoutError:
                    # Sem eventos novos: manda um "ping" (comentario SSE, linha
                    # iniciada por ":") so para manter a conexao viva.
                    yield ": ping\n\n"
        finally:
            # Quando o navegador fecha a aba, removemos sua fila da lista.
            if fila_do_cliente in clientes_conectados:
                clientes_conectados.remove(fila_do_cliente)

    return StreamingResponse(gerar_fluxo(), media_type="text/event-stream")
