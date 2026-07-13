from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_team, get_team_by_invite_code, add_member_to_team
from app.db.database import get_db_session
from app.dependencies import get_current_manager, get_current_user
from app.schemas import TeamCreate

teams_router = APIRouter(prefix='/teams', tags=['Команды'])


@teams_router.post('/create_team/')
async def register_team(
        new_team: TeamCreate,
        db: AsyncSession = Depends(get_db_session),
        current_user = Depends(get_current_manager)
):
    team = await create_team(name=new_team.name, db=db, current_user=current_user)
    return team


@teams_router.post('/join/{invite_code}')
async def join_team(
        invite_code: str,
        db: AsyncSession = Depends(get_db_session),
        current_user = Depends(get_current_user)
):
    team = await get_team_by_invite_code(invite_code=invite_code, db=db)
    if team is None:
        raise HTTPException(status_code=403, detail='Команды не существует')
    new_member = await add_member_to_team(current_user=current_user, team=team, db=db)

    return new_member