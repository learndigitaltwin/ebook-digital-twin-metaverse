# -*- coding: utf-8 -*-
"""
broker_local.py
--------------------------------------------------------------------------
Um broker MQTT rodando 100% em Python, escutando em 127.0.0.1:1883 — sem
precisar instalar o Mosquitto (ou qualquer outro binário externo) no
sistema. É o mesmo papel de "intermediário central" descrito no livro:

    "Os sensores publicam mensagens em tópicos hierárquicos [...] em um
     intermediário central chamado broker. Qualquer aplicação
     interessada, inclusive o gêmeo digital, assina esses tópicos e
     recebe as atualizações no momento em que ocorrem [...]." (seção 2.2)

Usa a biblioteca "amqtt" (asyncio nativo, puro Python). Todos os outros
scripts do pacote (sensor_simulador.py, monitor_mqtt.py,
ingestao_dashboard.py) continuam iguais — eles só enxergam "um broker em
127.0.0.1:1883", não importa se é o Mosquitto ou este broker em Python.

Uso:
    python broker_local.py
    python broker_local.py --host 127.0.0.1 --porta 1883

Pressione Ctrl+C para encerrar.
"""
import argparse
import asyncio
import logging

from amqtt.broker import Broker

logging.basicConfig(level=logging.WARNING)  # deixa o log do amqtt mais enxuto


def montar_config(host: str, porta: int) -> dict:
    """Configuração equivalente ao default_broker.yaml do amqtt, mas com o
    endereço/porta escolhidos e autenticação anônima liberada (adequado
    para um laboratório local, nunca para produção exposta à internet)."""
    return {
        "listeners": {
            "default": {
                "type": "tcp",
                "bind": f"{host}:{porta}",
            }
        },
        "plugins": {
            "amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": True},
            "amqtt.plugins.sys.broker.BrokerSysPlugin": {"sys_interval": 20},
        },
    }


async def executar(host: str, porta: int):
    broker = Broker(montar_config(host, porta))
    await broker.start()
    print(f"[broker] rodando em {host}:{porta} (Ctrl+C para parar)")
    try:
        await asyncio.Event().wait()  # mantém o broker no ar indefinidamente
    finally:
        print("\n[broker] encerrando...")
        await broker.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Broker MQTT local em Python (amqtt)")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço para escutar (padrão: 127.0.0.1)")
    parser.add_argument("--porta", type=int, default=1883, help="Porta para escutar (padrão: 1883)")
    args = parser.parse_args()

    try:
        asyncio.run(executar(args.host, args.porta))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
