from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import merchants, voice, query
from core.errors import app_exception_handler, AppException

app = FastAPI(title="Paytm VyaparSetu")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)

app.include_router(merchants.router, prefix="/api/v1/merchants", tags=["merchants"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])

@app.get("/health")
def health():
    return {"status": "ok"}
