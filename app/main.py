from fastapi import FastAPI

app = FastAPI(title="DevSecOps Demo Application")
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.get("/")
def root():
    return {"message": "DevSecOps demo application is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
