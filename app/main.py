from fastapi import FastAPI

from app.api.meetings import meet_router
from app.api.router import router
from app.api.tasks import task_router
from app.api.users import users_router, auth_router
from app.api.teams import teams_router
from app.ui.meetings import ui_meetings_router
from app.ui.tasks import ui_tasks_router
from app.ui.teams import ui_teams_router
from app.ui.users import ui_users_router

app = FastAPI()


@app.get('/health')
async def root():
    return {'status': 'healthy'}


app.include_router(router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(task_router)
app.include_router(meet_router)
app.include_router(ui_users_router)
app.include_router(ui_teams_router)
app.include_router(ui_tasks_router)
app.include_router(ui_meetings_router)
