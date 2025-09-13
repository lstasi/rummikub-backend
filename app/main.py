from fastapi import FastAPI

app = FastAPI(
    title="Rummikub Backend API",
    description="Backend API for Rummikub game",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "Rummikub Backend API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}