# -*- coding: utf-8 -*-
"""
monitor_sse.py
--------------------------------------------------------------------------
O "observador" bruto do stream SSE — o equivalente, para HTTP, do
monitor_mqtt.py: conecta em GET /eventos e imprime cada frame exatamente
como ele chega pela rede (linhas "event:" e "data:"), sem processar nada.

Uso:
    python monitor_sse.py
    python monitor_sse.py --host 127.0.0.1 --porta 8000
"""
import argparse
from datetime import datetime

import requests


def main():
    parser = argparse.ArgumentParser(description="Monitor bruto do stream SSE")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, default=8000)
    args = parser.parse_args()

    url = f"http://{args.host}:{args.porta}/eventos"
    print(f"[monitor] conectando em {url} — Ctrl+C para parar\n")

    while True:
        try:
            with requests.get(url, stream=True, timeout=(5, None)) as resp:
                for linha_bruta in resp.iter_lines(decode_unicode=True):
                    hora = datetime.now().strftime("%H:%M:%S")
                    if linha_bruta == "":
                        continue  # linha em branco que separa os frames SSE
                    if linha_bruta.startswith(":"):
                        print(f"{hora} | (comentário/keep-alive) {linha_bruta}")
                    else:
                        print(f"{hora} | {linha_bruta}")
        except requests.exceptions.RequestException as e:
            print(f"[monitor] conexão perdida ({e}); tentando de novo em 2s...")
            import time
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n[monitor] encerrado.")
            break


if __name__ == "__main__":
    main()
