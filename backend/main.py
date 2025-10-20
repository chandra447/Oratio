from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import agents, auth, chat, api_keys, knowledge_bases
from routers import voice_simple as voice  # Use simplified voice implementation

app = FastAPI(
    title="Oratio API",
    description="AI-Architected Voice Agents for Modern Enterprises",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(agents.router, prefix=settings.API_V1_PREFIX)
app.include_router(api_keys.router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_bases.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(voice.router, prefix=settings.API_V1_PREFIX)  # Voice WebSocket (simplified)


@app.get("/")
async def root():
    return {"message": "Oratio API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
