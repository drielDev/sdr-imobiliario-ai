from fastapi import FastAPI

from app.api.imoveis import router as imoveis_router


app = FastAPI(
    title="SDR Imobiliário AI",
    version="1.0.0"
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