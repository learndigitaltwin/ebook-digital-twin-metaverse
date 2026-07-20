# -*- coding: utf-8 -*-
"""
monitor_mqtt.py
--------------------------------------------------------------------------
Um "observador" bruto do broker: assina TODOS os tópicos (wildcard "#") e
imprime cada mensagem exatamente como ela chega, com tópico, QoS, a flag
de retained e o payload.

O objetivo deste script é permitir OBSERVAR o que está acontecendo dentro
do broker MQTT de forma independente do pipeline de ingestão/dashboard —
útil para depuração e para entender, na prática, a arquitetura descrita no
livro: "os sensores publicam via MQTT no broker; serviços de ingestão
assinam os tópicos, validam e persistem os dados" (seção 2.2).

Rode este script em um terminal separado, ao lado do sensor_simulador.py
e do ingestao_dashboard.py, para ver o tráfego bruto do broker em tempo
real, sem qualquer processamento.

Uso:
    python monitor_mqtt.py
    python monitor_mqtt.py --host localhost --porta 1883 --topico "fabrica/#"
"""
import argparse
import json
from datetime import datetime

import paho.mqtt.client as mqtt


def main():
    parser = argparse.ArgumentParser(description="Monitor bruto de tráfego MQTT")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--porta", type=int, default=1883)
    parser.add_argument("--topico", default="#", help='Filtro de tópicos (padrão: "#" = tudo)')
    args = parser.parse_args()

    def ao_conectar(cliente, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print(f"[monitor] conectado — assinando '{args.topico}' em {args.host}:{args.porta}")
            # Assina em QoS 2 (o teto): pelo padrão MQTT, a QoS efetiva de
            # cada mensagem entregue é min(QoS da publicação, QoS da
            # assinatura) — então assinar no teto deixa passar o valor
            # original de cada publicação (0, 1 ou 2) sem rebaixar nada.
            #
            # Observação: ao usar o broker_local.py (biblioteca "amqtt"),
            # esse cálculo de min() nem sempre é feito corretamente pela
            # biblioteca — em alguns casos ela reporta a QoS da assinatura
            # em vez da QoS original da publicação. Com um broker Mosquitto
            # tradicional esse comportamento é 100% fiel à especificação.
            # Não afeta a entrega dos dados, só o número de QoS exibido.
            cliente.subscribe(args.topico, qos=2)
        else:
            print(f"[monitor] falha ao conectar (codigo {reason_code})")

    def ao_receber(cliente, userdata, msg):
        hora = datetime.now().strftime("%H:%M:%S")
        try:
            corpo = json.loads(msg.payload.decode("utf-8"))
            corpo_fmt = json.dumps(corpo, ensure_ascii=False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            corpo_fmt = repr(msg.payload)

        retido = " [RETIDA]" if msg.retain else ""
        print(f"{hora} | tópico={msg.topic:<32} | qos={msg.qos}{retido} | payload={corpo_fmt}")

    cliente = mqtt.Client(
        client_id="monitor-observador",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    cliente.on_connect = ao_conectar
    cliente.on_message = ao_receber

    cliente.connect(args.host, args.porta, keepalive=30)
    print("[monitor] observando o broker — Ctrl+C para parar\n")
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("\n[monitor] encerrado.")


if __name__ == "__main__":
    main()
