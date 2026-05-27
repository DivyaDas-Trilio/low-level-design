from fastapi import FastAPI
import pdb; pdb.set_trace()
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, World!"}