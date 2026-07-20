import requests
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/api/telemetria"

def simular():
    logger.info("Iniciando simulador HTTP...")
    while True:
        try:
            # Simular Temperatura
            temp = random.uniform(60, 80)
            requests.post(API_URL, json={"topico": "temperatura", "valor": round(temp, 1), "unidade": "°C"})
            
            # Simular Vibração
            vib = random.uniform(1, 5)
            requests.post(API_URL, json={"topico": "vibracao", "valor": round(vib, 2), "unidade": "mm/s"})
            
            logger.info(f"Enviado: Temp={temp:.2f}, Vib={vib:.2f}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"Erro no simulador: {e}")
            time.sleep(5)

if __name__ == "__main__":
    simular()
