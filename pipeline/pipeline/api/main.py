from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pipeline.api.routes import lint, log, raw, status, sync


def create_app() -> FastAPI:
    app = FastAPI(title="Wiki Pipeline Operator")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(status.router, prefix="/api")
    app.include_router(lint.router, prefix="/api")
    app.include_router(sync.router, prefix="/api")
    app.include_router(raw.router, prefix="/api")
    app.include_router(log.router, prefix="/api")
    return app


app = create_app()
