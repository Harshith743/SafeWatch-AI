from api import app

# optional light health-check route (won't override existing routes):
@app.get("/__health")
async def __health():
    return {"status": "ok"}
