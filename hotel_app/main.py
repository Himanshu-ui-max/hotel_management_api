from fastapi import FastAPI

app = FastAPI(title="HIMS' Hotel Management")

@app.get("/")
async def get():
    return {"data" : "Hello wrold!!!"}

