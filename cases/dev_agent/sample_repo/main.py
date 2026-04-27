from fastapi import FastAPI

app = FastAPI(title="Sample Repo")


@app.get("/")
def root() -> dict:
    return {"status": "ok"}


@app.get("/items/{item_id}")
def get_item(item_id: int) -> dict:
    return {"item_id": item_id, "name": f"Item {item_id}"}
