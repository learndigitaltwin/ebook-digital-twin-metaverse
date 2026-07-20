# -*- coding: utf-8 -*-
"""
sensor_simulador.py
--------------------------------------------------------------------------
Simula um sensor de chão de fábrica publicando telemetria via MQTT, no
mesmo modelo publish/subscribe descrito no livro (Unidade II, seção 2.2):

    "Os sensores publicam mensagens em tópicos hierárquicos, como
     fabrica/linha1/motor3/temperatura, em um intermediário central
     chamado broker."

Este script publica periodicamente:
  - fabrica/linha1/motor3/temperatura   (QoS 0 — grandeza rápida, perda ok)
  - fabrica/linha1/motor3/vibracao      (QoS 1 — precisa chegar, duplicata ok)
  - fabrica/linha1/motor3/status        (QoS 2 + retained — estado do motor)

Também configura uma mensagem de "testamento" (Last Will and Testament),
exatamente como descrito no livro: um aviso automático que o broker envia
aos assinantes caso este script (o "dispositivo") caia de forma inesperada
(sem se desconectar corretamente).

Uso:
    python sensor_simulador.py
    python sensor_simulador.py --host localhost --porta 1883 --intervalo 2
"""
import argparse
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

TOPICO_BASE = "fabrica/linha1/motor3"


def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
    parser = argparse.ArgumentParser(description="Simulador de sensor MQTT (motor3)")
    parser.add_argument("--host", default="localhost", help="Endereço do broker MQTT")
    parser.add_argument("--porta", type=int, default=1883, help="Porta do broker MQTT")
    parser.add_argument("--intervalo", type=float, default=2.0, help="Segundos entre publicações")
    args = parser.parse_args()

    cliente = mqtt.Client(
        client_id="sensor-motor3",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    # ---- Last Will and Testament -------------------------------------
    # Se este processo cair sem chamar disconnect(), o broker publica esta
    # mensagem automaticamente no tópico de status, com retain=True, para
    # que qualquer novo assinante saiba imediatamente que o motor está
    # "offline" mesmo sem ter visto a queda acontecer.
    testamento = json.dumps({"estado": "offline", "motivo": "conexao_perdida", "ts": agora_iso()})
    cliente.will_set(f"{TOPICO_BASE}/status", payload=testamento, qos=2, retain=True)

    def ao_conectar(cliente, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print(f"[sensor] conectado ao broker {args.host}:{args.porta}")
            # Ao conectar (ou reconectar), publica-se o status "online",
            # substituindo o testamento retido de uma queda anterior.
            cliente.publish(
                f"{TOPICO_BASE}/status",
                json.dumps({"estado": "online", "ts": agora_iso()}),
                qos=2,
                retain=True,
            )
        else:
            print(f"[sensor] falha ao conectar (codigo {reason_code})")

    def ao_desconectar(cliente, userdata, flags, reason_code, properties=None):
        print("[sensor] desconectado do broker")

    cliente.on_connect = ao_conectar
    cliente.on_disconnect = ao_desconectar

    cliente.connect(args.host, args.porta, keepalive=30)
    cliente.loop_start()

    temperatura = 60.0  # ponto de partida, em graus Celsius
    print("[sensor] publicando telemetria — Ctrl+C para parar")
    try:
        while True:
            # ---- temperatura: caminha aleatoriamente, com leve tendência
            # de subida, simulando o aquecimento natural de um motor
            temperatura += random.uniform(-0.4, 0.6)
            temperatura = max(40.0, min(temperatura, 95.0))

            # ---- vibração: valor em mm/s, com ocasional pico (possível
            # sinal de desgaste de rolamento)
            vibracao = round(random.uniform(0.5, 2.5), 2)
            pico = random.random() < 0.08
            if pico:
                vibracao = round(random.uniform(6.0, 9.0), 2)

            payload_temp = json.dumps({"valor": round(temperatura, 1), "unidade": "C", "ts": agora_iso()})
            payload_vib = json.dumps({"valor": vibracao, "unidade": "mm/s", "ts": agora_iso()})

            # QoS 0: no máximo uma vez — aceitável para uma grandeza que
            # muda rápido e será atualizada de novo em poucos segundos.
            cliente.publish(f"{TOPICO_BASE}/temperatura", payload_temp, qos=0)

            # QoS 1: pelo menos uma vez — mais importante não perder o
            # dado (mesmo que uma duplicata eventualmente chegue).
            cliente.publish(f"{TOPICO_BASE}/vibracao", payload_vib, qos=1)

            alerta = " ⚠️  PICO DE VIBRAÇÃO" if pico else ""
            print(f"[sensor] temperatura={temperatura:5.1f}°C  vibracao={vibracao:4.2f}mm/s{alerta}")

            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\n[sensor] encerrando de forma limpa (envia disconnect, sem acionar o testamento)...")
        # Publica o status "offline" de forma explícita — uma desconexão
        # "limpa" não deveria depender do Last Will, que é só para quedas
        # inesperadas.
        cliente.publish(
            f"{TOPICO_BASE}/status",
            json.dumps({"estado": "offline", "motivo": "desligado_manualmente", "ts": agora_iso()}),
            qos=2,
            retain=True,
        )
        time.sleep(0.3)
        cliente.loop_stop()
        cliente.disconnect()


if __name__ == "__main__":
    main()
