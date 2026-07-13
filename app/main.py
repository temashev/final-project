from fastapi import FastAPI

from app.api.router import router
from app.api.users import users_router


app = FastAPI()


@app.get('/health')
async def root():
    return {'status': 'healthy'}


app.include_router(router)
app.include_router(users_router)
