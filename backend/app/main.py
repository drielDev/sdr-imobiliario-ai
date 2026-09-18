from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.imoveis import router as imoveis_router
from app.api.leads import router as leads_router

load_dotenv()


app = FastAPI(
    title="SDR Imobiliário AI",
    version="1.0.0"
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