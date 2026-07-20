# -*- coding: utf-8 -*-
"""
dashboard_app.py
--------------------------------------------------------------------------
Versão Otimizada do pipeline MQTT -> Dashboard.
"""
import argparse
import json
import threading
from collections import deque
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template_string

TOPICO_BASE = "fabrica/linha1/motor3"
MAX_HISTORICO = 60

app = Flask(__name__)

# ---------------------------------------------------------------- estado em memória
estado = {
    "temperatura": None,
    "vibracao": None,
    "status": {"estado": "desconhecido"},
    "ultima_atualizacao": None,
}
historico_temp = deque(maxlen=MAX_HISTORICO)
historico_vib = deque(maxlen=MAX_HISTORICO)
eventos = deque(maxlen=100)
trava = threading.Lock()

def validar_numero(corpo):
    return isinstance(corpo, dict) and isinstance(corpo.get("valor"), (int, float))

def registrar_evento(msg):
    agora = datetime.now().strftime("%H:%M:%S")
    eventos.append(f"[{agora}] {msg}")

# ---------------------------------------------------------------- cliente MQTT
def iniciar_mqtt(host, porta):
    def ao_conectar(cliente, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print(f"[dashboard] conectado ao broker {host}:{porta}")
            cliente.subscribe(f"{TOPICO_BASE}/temperatura", qos=0)
            cliente.subscribe(f"{TOPICO_BASE}/vibracao", qos=1)
            cliente.subscribe(f"{TOPICO_BASE}/status", qos=2)
            registrar_evento("Conectado ao Broker MQTT")
        else:
            print(f"[dashboard] falha ao conectar ao broker (codigo {reason_code})")

    def ao_receber(cliente, userdata, msg):
        try:
            corpo = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

        grandeza = msg.topic.rsplit("/", 1)[-1]
        with trava:
            if grandeza == "temperatura" and validar_numero(corpo):
                estado["temperatura"] = corpo
                historico_temp.append(corpo["valor"])
            elif grandeza == "vibracao" and validar_numero(corpo):
                estado["vibracao"] = corpo
                historico_vib.append(corpo["valor"])
            elif grandeza == "status":
                estado["status"] = corpo
                registrar_evento(f"Status alterado: {corpo.get('estado', 'desconhecido').upper()}")
            estado["ultima_atualizacao"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    cliente = mqtt.Client(client_id="dashboard-mqtt-final", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber
    cliente.connect(host, porta, keepalive=30)
    cliente.loop_start()
    return cliente

# ---------------------------------------------------------------- API REST
@app.route("/api/estado")
def api_estado():
    with trava:
        corpo = dict(estado)
        corpo["historico_temperatura"] = list(historico_temp)
        corpo["historico_vibracao"] = list(historico_vib)
        corpo["eventos"] = list(eventos)
        return jsonify(corpo)

# ---------------------------------------------------------------- Dashboard HTML
PAGINA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>MQTT Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  *{box-sizing:border-box}
  body{
    margin:0;background:#0a0f1c;color:#e8edf6;font-family:'Inter','Segoe UI',sans-serif;
    display:flex;flex-direction:column;min-height:100vh;
  }
  header{
    padding:1rem 2rem;border-bottom:1px solid #223052;display:flex;
    align-items:center;gap:1rem;background:#111a2e;
  }
  header h1{font-size:1.2rem;margin:0;flex-grow:1}
  #bolinha{width:.8rem;height:.8rem;border-radius:50%;background:#8ea0bf}
  #bolinha.online{background:#22c55e;box-shadow:0 0 8px #22c55e}
  #bolinha.offline{background:#ef4444;box-shadow:0 0 8px #ef4444}
  
  .container{padding:1.5rem;display:flex;flex-direction:column;gap:1.5rem}
  
  .grid-graficos{
    display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;
  }
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
    overflow-y:auto;flex:1;padding-right:0.5rem;
  }
  #log div{padding:.4rem 0;border-bottom:1px solid #1e293b}
  
  ::-webkit-scrollbar{width:8px}
  ::-webkit-scrollbar-track{background:#0a0f1c}
  ::-webkit-scrollbar-thumb{background:#223052;border-radius:4px}
</style>
</head>
<body>

<header>
  <h1>Dashboard (Motor) — <span style="color:#38bdf8">MQTT</span></h1>
  <div id="bolinha"></div>
  <span id="texto-status" style="color:#8ea0bf;font-size:.9rem">Conectando...</span>
</header>

<div class="container">
  <div class="grid-graficos">
    <div class="painel-grafico">
      <div class="cabecalho-mini">
        <span class="titulo-mini">Temperatura</span>
        <span class="valor-mini temp"><span id="v-temp">—</span> °C</span>
      </div>
      <div class="grafico-canvas" id="grafico-temp"></div>
    </div>
    <div class="painel-grafico">
      <div class="cabecalho-mini">
        <span class="titulo-mini">Vibração</span>
        <span class="valor-mini vib"><span id="v-vib">—</span> mm/s</span>
      </div>
      <div class="grafico-canvas" id="grafico-vib"></div>
    </div>
  </div>

  <div class="painel-eventos">
    <h2>Eventos do Sistema (MQTT)</h2>
    <div id="log"></div>
  </div>
</div>

<script>
'use strict';

let ultimoLogCount = 0;
let graficoOk = false;

function getLayout(cor, unidade) {
  return {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#8ea0bf', size: 11 },
    margin: { t: 10, r: 10, l: 40, b: 30 },
    hovermode: 'x unified',
    xaxis: { gridcolor: '#1e293b', showticklabels: false, zeroline: false },
    yaxis: { title: unidade, gridcolor: '#1e293b', zeroline: false },
    showlegend: false
  };
}

const configBase = { displayModeBar: false, responsive: true };

function inicializarGraficos(temps, vibs) {
  const xT = temps.map((_, i) => i);
  const xV = vibs.map((_, i) => i);

  Plotly.newPlot('grafico-temp', [{
    x: xT, y: temps, type: 'scatter', mode: 'lines',
    line: { color: '#38bdf8', width: 3, shape: 'spline' },
    fill: 'tozeroy', fillcolor: 'rgba(56, 189, 248, 0.1)'
  }], getLayout('#38bdf8', '°C'), configBase);

  Plotly.newPlot('grafico-vib', [{
    x: xV, y: vibs, type: 'scatter', mode: 'lines',
    line: { color: '#f472b6', width: 3, shape: 'spline' },
    fill: 'tozeroy', fillcolor: 'rgba(244, 114, 182, 0.1)'
  }], getLayout('#f472b6', 'mm/s'), configBase);
  
  graficoOk = true;
}

async function atualizar(){
  try{
    const r = await fetch('/api/estado');
    const d = await r.json();
    
    if(d.temperatura) document.getElementById('v-temp').textContent = d.temperatura.valor.toFixed(1);
    if(d.vibracao) document.getElementById('v-vib').textContent = d.vibracao.valor.toFixed(2);
    
    const online = d.status && d.status.estado === 'online';
    document.getElementById('bolinha').className = online ? 'online' : 'offline';
    document.getElementById('texto-status').textContent = online ? 'Motor Online' : 'Motor Offline';

    if(!graficoOk) {
      inicializarGraficos(d.historico_temperatura || [], d.historico_vibracao || []);
    } else {
      const xT = d.historico_temperatura.map((_, i) => i);
      const xV = d.historico_vibracao.map((_, i) => i);
      Plotly.update('grafico-temp', { x: [xT], y: [d.historico_temperatura] });
      Plotly.update('grafico-vib', { x: [xV], y: [d.historico_vibracao] });
    }

    if(d.eventos && d.eventos.length !== ultimoLogCount) {
      const log = document.getElementById('log');
      log.innerHTML = d.eventos.map(e => `<div>${e}</div>`).join('');
      log.scrollTop = log.scrollHeight;
      ultimoLogCount = d.eventos.length;
    }
  } catch(e) {
    document.getElementById('texto-status').textContent = 'Erro na conexão...';
  }
}

setInterval(atualizar, 1000);
atualizar();
</script>
</body>
</html>
"""

@app.route("/")
def pagina_dashboard():
    return render_template_string(PAGINA)

def main():
    parser = argparse.ArgumentParser(description="Dashboard MQTT Otimizado")
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-porta", type=int, default=1883)
    parser.add_argument("--http-porta", type=int, default=5000)
    args = parser.parse_args()

    iniciar_mqtt(args.mqtt_host, args.mqtt_porta)
    print(f"[dashboard] disponível em http://localhost:{args.http_porta}")
    app.run(host="0.0.0.0", port=args.http_porta, debug=False, threaded=True)

if __name__ == "__main__":
    main()
