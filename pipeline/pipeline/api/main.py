from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pipeline.api.routes import graph, jobs, lint, log, raw, status, sync, upload, wiki


def create_app() -> FastAPI:
    app = FastAPI(title="Wiki Pipeline Operator")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(status.router, prefix="/api")
    app.include_router(lint.router, prefix="/api")
    app.include_router(sync.router, prefix="/api")
    app.include_router(raw.router, prefix="/api")
    app.include_router(log.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(graph.router, prefix="/api")
    app.include_router(upload.router, prefix="/api")
    app.include_router(wiki.router, prefix="/api")
    return app


app = create_app()
