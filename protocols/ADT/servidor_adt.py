# -*- coding: utf-8 -*-
"""
servidor_adt.py
--------------------------------------------------------------------------
Emulador de Azure Digital Twins (ADT) com suporte a DTDL e atualização via PATCH/POST.
"""
import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Azure Digital Twins Emulator")

# ---------------------------------------------------------------- Estado do Gêmeo (Twin)
# No ADT, o gêmeo é uma instância de um modelo DTDL
digital_twin = {
    "$dtId": "motor3",
    "$metadata": {"$model": "dtmi:fabrica:motor;1"},
    "temperatura": 0.0,
    "vibracao": 0.0,
    "status": "desconhecido",
    "$lastUpdate": None
}

historico_temp = deque(maxlen=60)
historico_vib = deque(maxlen=60)
assinantes = []

def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

async def transmitir(nome_evento, corpo_dict):
    linha = {"evento": nome_evento, "dado": corpo_dict}
    mortas = []
    for fila in assinantes:
        try:
            fila.put_nowait(linha)
        except asyncio.QueueFull:
            mortas.append(fila)
    for fila in mortas:
        if fila in assinantes:
            assinantes.remove(fila)

# ---------------------------------------------------------------- API ADT (Simulada)
class PropertyUpdate(BaseModel):
    op: str = "replace"
    path: str
    value: float | str

@app.patch("/digitaltwins/{id}", status_code=204)
async def update_twin(id: str, patch: List[PropertyUpdate]):
    """Emula a API de atualização de propriedades do Azure Digital Twins."""
    global digital_twin
    if id != digital_twin["$dtId"]:
        return JSONResponse({"error": "Twin not found"}, status_code=404)

    for update in patch:
        prop = update.path.strip("/")
        if prop in ["temperatura", "vibracao", "status"]:
            digital_twin[prop] = update.value
            if prop == "temperatura":
                historico_temp.append(update.value)
            elif prop == "vibracao":
                historico_vib.append(update.value)
            
            # Notifica o dashboard via SSE
            await transmitir("property_update", {"property": prop, "value": update.value, "ts": agora_iso()})

    digital_twin["$lastUpdate"] = agora_iso()
    return

@app.get("/digitaltwins/{id}")
async def get_twin(id: str):
    """Retorna o estado completo do gêmeo."""
    if id != digital_twin["$dtId"]:
        return JSONResponse({"error": "Twin not found"}, status_code=404)
    
    corpo = dict(digital_twin)
    corpo["historico_temperatura"] = list(historico_temp)
    corpo["historico_vibracao"] = list(historico_vib)
    return corpo

@app.get("/eventos")
async def eventos(request: Request):
    fila: asyncio.Queue = asyncio.Queue(maxsize=100)
    assinantes.append(fila)

    async def gerador():
        try:
            snapshot = dict(digital_twin)
            snapshot["historico_temperatura"] = list(historico_temp)
            snapshot["historico_vibracao"] = list(historico_vib)
            yield f"event: estado_inicial\ndata: {json.dumps(snapshot)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(fila.get(), timeout=15)
                    yield f"event: {item['evento']}\ndata: {json.dumps(item['dado'])}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if fila in assinantes:
                assinantes.remove(fila)

    return StreamingResponse(gerador(), media_type="text/event-stream")

# ---------------------------------------------------------------- Dashboard
PAGINA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Azure Digital Twins Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  *{box-sizing:border-box}
  body{
    margin:0;background:#0a0f1c;color:#e8edf6;font-family:'Segoe UI',sans-serif;
    display:flex;flex-direction:column;min-height:100vh;
  }
  header{
    padding:1rem 2rem;border-bottom:1px solid #223052;display:flex;
    align-items:center;gap:1rem;background:#111a2e;
  }
  header h1{font-size:1.2rem;margin:0;flex-grow:1}
  .badge-adt{background:#0078d4;color:white;padding:.2rem .6rem;border-radius:4px;font-size:.7rem;font-weight:700}
  
  .container{padding:1.5rem;display:flex;flex-direction:column;gap:1.5rem}
  
  .grid-graficos{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
  .painel-grafico{
    background:#111a2e;border-radius:12px;padding:1rem;border:1px solid #223052;
    display:flex;flex-direction:column;height:350px;
  }
  .cabecalho-mini{display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem}
  .titulo-mini{font-size:.8rem;color:#8ea0bf;text-transform:uppercase;font-weight:600}
  .valor-mini{font-size:1.4rem;font-weight:700}
  .valor-mini.temp{color:#38bdf8}
  .valor-mini.vib{color:#f472b6}
  .grafico-canvas{flex:1;min-height:0}

  .painel-eventos{
    background:#111a2e;border-radius:12px;padding:1rem;border:1px solid #223052;
    display:flex;flex-direction:column;height:300px;
  }
  .painel-eventos h2{margin:0 0 1rem;font-size:.9rem;color:#8ea0bf;text-transform:uppercase}
  #log{
    font-family:ui-monospace,Consolas,monospace;font-size:.85rem;color:#8ea0bf;
    overflow-y:auto;flex:1;
  }
  #log div{padding:.4rem 0;border-bottom:1px solid #1e293b}
  #log span.property{color:#38bdf8;font-weight:600}
</style>
</head>
<body>

<header>
  <h1>Dashboard (Motor) — <span style="color:#38bdf8">Azure Digital Twins</span></h1>
  <div class="badge-adt">MODEL: fabrica:motor;1</div>
  <span id="texto-status" style="color:#8ea0bf;font-size:.9rem">Conectando...</span>
</header>

<div class="container">
  <div class="grid-graficos">
    <div class="painel-grafico">
      <div class="cabecalho-mini">
        <span class="titulo-mini">Property: Temperatura</span>
        <span class="valor-mini temp"><span id="v-temp">—</span> °C</span>
      </div>
      <div class="grafico-canvas" id="grafico-temp"></div>
    </div>
    <div class="painel-grafico">
      <div class="cabecalho-mini">
        <span class="titulo-mini">Property: Vibração</span>
        <span class="valor-mini vib"><span id="v-vib">—</span> mm/s</span>
      </div>
      <div class="grafico-canvas" id="grafico-vib"></div>
    </div>
  </div>

  <div class="painel-eventos">
    <h2>Property Update Log (Azure Digital Twins API)</h2>
    <div id="log"></div>
  </div>
</div>

<script>
'use strict';

let xTemp = [], yTemp = [], xVib = [], yVib = [];
let graficoOk = false;

function logar(msg) {
  const log = document.getElementById('log');
  const div = document.createElement('div');
  div.innerHTML = msg;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function getLayout(unidade) {
  return {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#8ea0bf', size: 11 },
    margin: { t: 10, r: 10, l: 40, b: 30 },
    hovermode: 'x unified',
    xaxis: { gridcolor: '#1e293b', showticklabels: false },
    yaxis: { title: unidade, gridcolor: '#1e293b' },
    showlegend: false
  };
}

function inicializarGraficos(temps, vibs) {
  xTemp = temps.map((_, i) => i);
  yTemp = temps;
  xVib = vibs.map((_, i) => i);
  yVib = vibs;

  Plotly.newPlot('grafico-temp', [{
    x: xTemp, y: yTemp, type: 'scatter', mode: 'lines',
    line: { color: '#38bdf8', width: 3, shape: 'spline' },
    fill: 'tozeroy', fillcolor: 'rgba(56, 189, 248, 0.1)'
  }], getLayout('°C'), { responsive: true, displayModeBar: false });

  Plotly.newPlot('grafico-vib', [{
    x: xVib, y: yVib, type: 'scatter', mode: 'lines',
    line: { color: '#f472b6', width: 3, shape: 'spline' },
    fill: 'tozeroy', fillcolor: 'rgba(244, 114, 182, 0.1)'
  }], getLayout('mm/s'), { responsive: true, displayModeBar: false });
  
  graficoOk = true;
}

const fonte = new EventSource('/eventos');

fonte.addEventListener('estado_inicial', (e) => {
  const d = JSON.parse(e.data);
  document.getElementById('v-temp').textContent = d.temperatura.toFixed(1);
  document.getElementById('v-vib').textContent = d.vibracao.toFixed(2);
  document.getElementById('texto-status').textContent = 'Twin Sync OK';
  inicializarGraficos(d.historico_temperatura || [], d.historico_vibracao || []);
  logar(`Twin <b>${d.$dtId}</b> carregado com sucesso.`);
});

fonte.addEventListener('property_update', (e) => {
  const d = JSON.parse(e.data);
  if (d.property === 'temperatura') {
    document.getElementById('v-temp').textContent = d.value.toFixed(1);
    yTemp.push(d.value); xTemp.push(xTemp.length);
    if (yTemp.length > 60) { yTemp.shift(); xTemp.shift(); }
    Plotly.update('grafico-temp', { x: [xTemp], y: [yTemp] });
  } else if (d.property === 'vibracao') {
    document.getElementById('v-vib').textContent = d.value.toFixed(2);
    yVib.push(d.value); xVib.push(xVib.length);
    if (yVib.length > 60) { yVib.shift(); xVib.shift(); }
    Plotly.update('grafico-vib', { x: [xVib], y: [yVib] });
  }
  logar(`[${d.ts}] PATCH /digitaltwins/motor3 update: <span class="property">${d.property}</span> = ${d.value}`);
});
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGINA
