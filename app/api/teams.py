from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_team, get_team_by_invite_code, add_member_to_team, get_team_by_team_id, \
    remove_member_from_team
from app.db.database import get_db_session
from app.dependencies import get_current_manager, get_current_user
from app.schemas import TeamCreate

teams_router = APIRouter(prefix='/teams', tags=['Команды'])


@teams_router.post('/create_team/')
async def register_team(
        new_team: TeamCreate,
        db: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_manager)
):
    team = await create_team(name=new_team.name, db=db, current_user=current_user)
    return team


@teams_router.post('/{invite_code}/join/')
async def join_team(
        invite_code: str,
        db: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    team = await get_team_by_invite_code(invite_code=invite_code, db=db)
    if team is None:
        raise HTTPException(status_code=403, detail='Команды не существует')
    new_member = await add_member_to_team(current_user=current_user, team=team, db=db)

    return new_member


@teams_router.get('/{team_id}/members/')
async def get_team_members(
        team_id: int,
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    team = await get_team_by_team_id(team_id=team_id, db=db, current_user=current_user)
    if not team:
        raise HTTPException(status_code=404, detail=f'Команды с id:{team_id} не существует')
    return team


@teams_router.delete('/{team_id}/members/{user_id}')
async def delete_team_member(
        team_id: int,
        user_id: int,
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    team = await remove_member_from_team(team_id=team_id, current_user=current_user, user_id=user_id, db=db)
    if not team:
        raise HTTPException(status_code=404, detail=f'Команды с id:{team_id} не существует')
    return team

## TODO: реализовать смену роли (менять может только менеджер)