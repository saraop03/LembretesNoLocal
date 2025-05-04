
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from geopy.distance import geodesic
import time
import json
import os

from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import credentials, messaging, firestore, initialize_app


app = FastAPI()
lembretes = []
historico = {}

firebase_json = os.getenv("FIREBASE_JSON")
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
    for doc in docs:
        lembrete = doc.to_dict()
        distancia = geodesic(user_location, (lembrete['latitude'], lembrete['longitude'])).meters
        margem = 100 + velocidade * 5
        if distancia <= margem:
            proximos.append(lembrete)

    return proximos

def verificar_todos_utilizadores():
    print("Verificação automática a correr...")

scheduler = BackgroundScheduler()
scheduler.add_job(verificar_todos_utilizadores, 'interval', seconds=60)
scheduler.start()
