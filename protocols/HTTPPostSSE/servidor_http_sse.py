import asyncio
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gêmeo Digital - HTTP/SSE Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de clientes conectados ao SSE
subscribers: List[asyncio.Queue] = []

class Telemetria(BaseModel):
    topico: str
    valor: float
    unidade: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Gêmeo Digital - HTTP/SSE</title>
        <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0a0f1c;
                --painel: #111a2e;
                --borda: #1e293b;
                --texto: #f1f5f9;
                --accent: #0078d4;
            }
            body { 
                font-family: 'Inter', sans-serif; 
                background: var(--bg); 
                color: var(--texto); 
                margin: 0; padding: 20px;
            }
            .header { text-align: center; margin-bottom: 30px; }
            .charts-container { 
                display: flex; 
                gap: 20px; 
                margin-bottom: 20px;
            }
            .chart-card { 
                flex: 1; 
                background: var(--painel); 
                border: 1px solid var(--borda); 
                border-radius: 12px; 
                padding: 15px;
                height: 400px;
            }
            .events-panel {
                background: var(--painel);
                border: 1px solid var(--borda);
                border-radius: 12px;
                padding: 15px;
                height: 300px;
                display: flex;
                flex-direction: column;
            }
            .events-title { font-weight: 700; margin-bottom: 10px; color: var(--accent); }
            #event-log {
                flex: 1;
                overflow-y: auto;
                font-family: monospace;
                font-size: 13px;
                padding: 10px;
                background: #070c18;
                border-radius: 6px;
                line-height: 1.5;
            }
            .event-entry { border-bottom: 1px solid #1e293b; padding: 4px 0; }
            .timestamp { color: #64748b; margin-right: 8px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Monitoramento em Tempo Real (HTTP/SSE)</h1>
            <p>Sincronização bidirecional entre o ativo físico e o dashboard digital</p>
        </div>

        <div class="charts-container">
            <div class="chart-card" id="chart-temp"></div>
            <div class="chart-card" id="chart-vib"></div>
        </div>

        <div class="events-panel">
            <div class="events-title">LOG DE EVENTOS SSE</div>
            <div id="event-log"></div>
        </div>

        <script>
            const layoutBase = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#f1f5f9', family: 'Inter' },
                margin: { t: 40, r: 20, b: 40, l: 40 },
                xaxis: { gridcolor: '#1e293b', zeroline: false },
                yaxis: { gridcolor: '#1e293b', zeroline: false }
            };

            const config = { responsive: true, displayModeBar: false };

            let xData = [];
            let yTemp = [];
            let yVib = [];

            Plotly.newPlot('chart-temp', [{
                x: xData, y: yTemp, type: 'scatter', mode: 'lines',
                name: 'Temperatura', line: { color: '#0078d4', shape: 'spline' }, fill: 'tozeroy'
            }], { ...layoutBase, title: 'Temperatura (°C)' }, config);

            Plotly.newPlot('chart-vib', [{
                x: xData, y: yVib, type: 'scatter', mode: 'lines',
                name: 'Vibração', line: { color: '#f472b6', shape: 'spline' }, fill: 'tozeroy'
            }], { ...layoutBase, title: 'Vibração (mm/s)' }, config);

            const eventSource = new EventSource("/stream");
            const logEl = document.getElementById('event-log');

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const time = new Date().toLocaleTimeString();

                if (data.topico === 'temperatura') {
                    Plotly.extendTraces('chart-temp', { x: [[time]], y: [[data.valor]] }, [0]);
                } else if (data.topico === 'vibracao') {
                    Plotly.extendTraces('chart-vib', { x: [[time]], y: [[data.valor]] }, [0]);
                }

                // Log
                const entry = document.createElement('div');
                entry.className = 'event-entry';
                entry.innerHTML = `<span class="timestamp">[${time}]</span> <span style="color:#22c55e">DADO RECEBIDO:</span> ${event.data}`;
                logEl.prepend(entry);
            };
        </script>
    </body>
    </html>
    """

@app.post("/api/telemetria")
async def update_data(msg: Telemetria):
    data = msg.dict()
    logger.info(f"Recebido: {data}")
    
    # Notificar todos os assinantes SSE
    msg_json = json.dumps(data)
    for queue in subscribers:
        await queue.put(msg_json)
    
    return {"status": "ok"}

@app.get("/stream")
async def stream(request: Request):
    queue = asyncio.Queue()
    subscribers.append(queue)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
