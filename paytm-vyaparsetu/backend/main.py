from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import merchants, voice, query, challan, internal, alerts, ledger, payments
from api.deps import request_id_middleware
from core.errors import app_exception_handler, AppException

app = FastAPI(title="Paytm VyaparSetu")

app.middleware("http")(request_id_middleware)

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
app.include_router(challan.router, prefix="/api/v1/challan", tags=["challan"])
app.include_router(internal.router, prefix="/api/v1/internal", tags=["internal"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(ledger.router, prefix="/api/v1/ledger", tags=["ledger"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])


@app.get("/health")
def health():
    return {"status": "ok"}
