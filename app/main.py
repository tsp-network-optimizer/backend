from fastapi import FastAPI

app = FastAPI()

@app.get("/prueba")
def prueba():
    return {"message": "prueba"}
