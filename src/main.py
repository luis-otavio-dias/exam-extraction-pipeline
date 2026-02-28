import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router as api_router
from config import CONFIG
from models.question import ProcessingResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Exam Extraction API",
    description=(
        "Microservice that extracts structured exam data from PDFs "
        "using LLM-powered pipelines."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.api.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["X-Api-Key", "Content-Type"],
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled exception")
    body = ProcessingResponse(
        status="error",
        error_message=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content=body.model_dump(),
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "exam-extraction-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
