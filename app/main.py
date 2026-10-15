from fastapi import FastAPI

app = FastAPI(title="DevSecOps Demo Application")


@app.get("/")
def root():
    return {"message": "DevSecOps demo application is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
