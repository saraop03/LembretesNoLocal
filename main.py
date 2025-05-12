from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from geopy.distance import geodesic
import time
import json
import os
import requests

from fastapi.responses import JSONResponse
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import credentials, firestore

app = FastAPI()
lembretes = []
historico = {}

# 🔐 Firebase setup
firebase_json = os.getenv("FIREBASE_JSON")
if not firebase_json:
    raise ValueError("FIREBASE_JSON não está definido nas variáveis de ambiente")

cred = credentials.Certificate(json.loads(firebase_json))
firebase_admin.initialize_app(cred)
db = firestore.client()

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# 📤 Enviar notificação via Expo
def enviar_notificacao_expo(token, title, body):
    if not token.startswith("ExponentPushToken"):
        print(f"❌ Token inválido: {token}")
        return

    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default"
    }

    try:
        response = requests.post(EXPO_PUSH_URL, json=payload)
        print(f"📬 Expo status: {response.status_code} | {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar via Expo: {e}")

# 📌 Modelos
class Lembrete(BaseModel):
    mensagem: str
    latitude: float
    longitude: float
    ativo: bool = True

class Token(BaseModel):
    token: str

# 📝 Guardar lembrete
@app.post("/lembretes")
def criar_lembrete(lembrete: Lembrete):
    db.collection("lembretes").add(lembrete.dict())
    return {"status": "lembrete guardado"}

@app.patch("/lembretes/{lembrete_id}/desativar")
def desativar_lembrete(lembrete_id: str):
    try:
        ref = db.collection("lembretes").document(lembrete_id)
        ref.update({"ativo": False})
        return {"status": "lembrete desativado"}
    except Exception as e:
        print(f"❌ Erro ao desativar lembrete: {e}")
        return JSONResponse(status_code=500, content={"detail": "Erro ao desativar lembrete"})


@app.post("/tokens")
def registar_token(token: Token):
    try:
        # Verifique se o token é válido antes de tentar salvar
        if not token.token or not isinstance(token.token, str):
            return JSONResponse(status_code=400, content={"detail": "Token inválido"})
        print(f"Registrando token: {token.token}")
        # Registre o token no Firestore
        db.collection("tokens").add(token.dict())
        return {"status": "token registado com sucesso"}

    except Exception as e:
        print(f"Erro ao registrar o token: {e}")
        return JSONResponse(status_code=500, content={"detail": "Erro ao registrar token"})


# 📍 Verificar localização e enviar notificações se necessário
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
            if not lembrete.get("ativo", True):
                continue  # ignorar lembretes inativos
        
            distancia = geodesic(user_location, (lembrete['latitude'], lembrete['longitude'])).meters
            margem = 100 + velocidade * 5
            if distancia <= margem:
                lembrete["id"] = doc.id
                proximos.append(lembrete)
        
                tokens_ref = db.collection("tokens").stream()
                for token_doc in tokens_ref:
                    token_data = token_doc.to_dict()
                    token = token_data.get("token")
                    if token:
                        enviar_notificacao_expo(token, "📍 Estás perto de um lembrete!", lembrete["mensagem"])


        print("✅ Verificação concluída com sucesso")
        return proximos

    except Exception as e:
        print("❌ ERRO INTERNO no /verificar:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": "Erro interno"})

# 🕒 Agendamento de verificação (placeholder)
def verificar_todos_utilizadores():
    print("Verificação automática a correr...")

scheduler = BackgroundScheduler()
scheduler.add_job(verificar_todos_utilizadores, 'interval', seconds=60)
scheduler.start()
