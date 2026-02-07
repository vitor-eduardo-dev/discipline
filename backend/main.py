from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import os

# -----------------------------------------
# A.3 — carregar .env automaticamente
# -----------------------------------------
from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis do arquivo .env

from database import Base, engine
from routers import habits, progress, auth
from routers.dashboard import router as dashboard_router
from database import SessionLocal
from services.achievement_engine import create_default_achievements

# -----------------------------------------
# A.4 — ENV (dev/prod) para ligar/desligar docs
# -----------------------------------------
ENV = os.getenv("ENV", "dev")  # dev | prod

# -----------------------------------------
# 1) Criar app primeiro (sem quebrar contratos)
# -----------------------------------------
app = FastAPI(
    title="Discipline API",
    version="1.0",
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

# -----------------------------------------
# A.4 — Trusted Hosts (hardening mínimo)
# -----------------------------------------
trusted_env = os.getenv("TRUSTED_HOSTS", "")
trusted_hosts = [h.strip() for h in trusted_env.split(",") if h.strip()]

# fallback seguro (dev local)
if not trusted_hosts:
    trusted_hosts = ["127.0.0.1", "localhost"]

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# -----------------------------------------
# 2) CORS (mínimo necessário para frontend)
# -----------------------------------------
cors_env = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in cors_env.split(",") if o.strip()]

# fallback seguro (dev) caso não exista .env
if not origins:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------
# 3) Registrar routers
# -----------------------------------------
app.include_router(habits.router)
app.include_router(progress.router)
app.include_router(dashboard_router)
app.include_router(auth.router)

# -----------------------------------------
# 4) Criar tabelas
# -----------------------------------------
Base.metadata.create_all(bind=engine)

db = SessionLocal()
create_default_achievements(db)
db.close()

# -----------------------------------------
# 5) Rota de teste
# -----------------------------------------
@app.get("/")
def root():
    return {"message": "API funcionando"}
