
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from geopy.distance import geodesic
import time
import json
import os

from fastapi.responses import JSONResponse
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import credentials, messaging, firestore, initialize_app


app = FastAPI()
lembretes = []
historico = {}

firebase_json = os.getenv("FIREBASE_JSON")
if not firebase_json:
    raise ValueError("FIREBASE_JSON não está definido nas variáveis de ambiente")

cred = credentials.Certificate(json.loads(firebase_json))
firebase_admin.initialize_app(cred)
db = firestore.client()

class Lembrete(BaseModel):
    mensagem: str
    latitude: float
    longitude: float

@app.post("/lembretes")
def criar_lembrete(lembrete: Lembrete):
    db.collection("lembretes").add(lembrete.dict())
    return {"status": "lembrete guardado"}

@app.get("/verificar/{lat}/{lon}")
def verificar(lat: float, lon: float):
    try:
        print("✅ Endpoint /verificar chamado")
        user_id = "user1"
        now = time.time()
        user_location = (lat, lon)

        if user_id in historico:
            dist = geodesic(user_location, historico[user_id]['pos']).meters
            tempo = now - historico[user_id]['timestamp']
            velocidade = dist / tempo if tempo > 0 else 0
        else:
            velocidade = 1

        historico[user_id] = {'pos': user_location, 'timestamp': now}

        proximos = []
        docs = db.collection("lembretes").stream()
        print("🔍 A ler lembretes do Firestore")

        for doc in docs:
            lembrete = doc.to_dict()
            distancia = geodesic(user_location, (lembrete['latitude'], lembrete['longitude'])).meters
            margem = 100 + velocidade * 5
            if distancia <= margem:
                proximos.append(lembrete)

        print("✅ Verificação concluída com sucesso")
        return proximos

    except Exception as e:
        print("❌ ERRO INTERNO no /verificar:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": "Erro interno"})

def verificar_todos_utilizadores():
    print("Verificação automática a correr...")

scheduler = BackgroundScheduler()
scheduler.add_job(verificar_todos_utilizadores, 'interval', seconds=60)
scheduler.start()
