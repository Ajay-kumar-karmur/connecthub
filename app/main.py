from fastapi import FastAPI

app = FastAPI(title="ConnectHub")


@app.get("/health")
def health():
    return {"status": "ok"}
