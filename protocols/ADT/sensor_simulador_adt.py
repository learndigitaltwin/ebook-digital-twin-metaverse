# -*- coding: utf-8 -*-
"""
sensor_simulador_adt.py
--------------------------------------------------------------------------
Simulador de sensor que envia atualizações para o Azure Digital Twins (ADT).
Utiliza o formato JSON Patch (op: replace) para atualizar propriedades.
"""
import argparse
import random
import time
import requests

def main():
    parser = argparse.ArgumentParser(description="Simulador de Sensor para Azure Digital Twins")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--intervalo", type=float, default=2.0)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.porta}/digitaltwins/motor3"

    print(f"[sensor] Iniciando simulação ADT para {base_url}")
    
    temperatura = 60.0
    
    try:
        while True:
            # Simulação de dados
            temperatura += random.uniform(-0.5, 0.7)
            temperatura = max(40.0, min(temperatura, 95.0))
            vibracao = round(random.uniform(0.5, 3.0), 2)
            
            # Formato JSON Patch (Azure Digital Twins padrão)
            patch_data = [
                {"op": "replace", "path": "/temperatura", "value": round(temperatura, 1)},
                {"op": "replace", "path": "/vibracao", "value": vibracao},
                {"op": "replace", "path": "/status", "value": "online"}
            ]
            
            try:
                # O Azure Digital Twins usa o método PATCH para atualizações de propriedades
                r = requests.patch(base_url, json=patch_data, timeout=3)
                print(f"[sensor] PATCH Property Update -> HTTP {r.status_code} | Temp: {temperatura:.1f} | Vib: {vibracao:.2f}")
            except Exception as e:
                print(f"[sensor] Erro ao conectar ao ADT: {e}")

            time.sleep(args.intervalo)
            
    except KeyboardInterrupt:
        print("\n[sensor] Simulação encerrada.")

if __name__ == "__main__":
    main()
