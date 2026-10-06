import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api.chat import router as chat_router
from app.api.dashboard import router as dashboard_router
from app.api.imoveis import router as imoveis_router
from app.api.leads import router as leads_router
from app.integracao.followup import loop_followup

logging.basicConfig(level=logging.INFO)

# 0 desliga o job de follow-up automático.
INTERVALO_FOLLOWUP_SEGUNDOS = float(os.getenv("FOLLOWUP_INTERVALO_SEGUNDOS", "60"))


@asynccontextmanager
async def lifespan(app: FastAPI):

    tarefa_followup = (
        asyncio.create_task(loop_followup(INTERVALO_FOLLOWUP_SEGUNDOS))
        if INTERVALO_FOLLOWUP_SEGUNDOS > 0
        else None
    )

    yield

    if tarefa_followup is not None:
        tarefa_followup.cancel()
        with suppress(asyncio.CancelledError):
            await tarefa_followup


app = FastAPI(
    title="SDR Imobiliário AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():

    return {
        "message": "API no ar. Acesse /docs para ver a documentação."
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


app.include_router(
    imoveis_router
)

app.include_router(
    chat_router
)

app.include_router(
    leads_router
)

app.include_router(
    dashboard_router
)