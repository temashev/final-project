from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.teams import create_team, get_team_by_invite_code, check_user_in_team, add_member_to_team
from app.services.teams import remove_member_from_team, update_members_role, get_team_by_team_id, leave_team
from app.db.database import get_db_session
from app.dependencies import get_current_manager, get_current_user
from app.schemas import TeamCreate, UpdateRoleRequest, TeamMembersResponse, TeamMemberResponse

teams_router = APIRouter(prefix='/teams', tags=['Команды'])


@teams_router.post('/create_team/', response_model=TeamMembersResponse)
async def register_team(
        new_team: TeamCreate,
        db: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_manager)
):
    team = await create_team(name=new_team.name, db=db, current_user=current_user)
    return team


@teams_router.post('/{invite_code}/join/', response_model=TeamMemberResponse)
async def join_team(
        invite_code: str,
        db: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_user)
):
    team = await get_team_by_invite_code(invite_code=invite_code, db=db)
    if team is None:
        raise HTTPException(status_code=403, detail='Команды не существует')
    if await check_user_in_team(team_id=team.id, user_id=current_user.id, db=db):
        raise HTTPException(status_code=409, detail='Вы уже в этой команде')
    new_member = await add_member_to_team(current_user=current_user, team=team, db=db)

    return new_member


@teams_router.get('/{team_id}/members/', response_model=TeamMembersResponse)
async def get_team_members(
        team_id: int = Path(le=2147483647, ge=1),  # чтобы не было 500 ошибки при больших или числах <0
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    team = await get_team_by_team_id(team_id=team_id, db=db, current_user=current_user)
    if not team:
        raise HTTPException(status_code=404, detail=f'Команды с id:{team_id} не существует')
    return team


@teams_router.delete('/{team_id}/members/{user_id}/', response_model=TeamMembersResponse)
async def delete_team_member(
        team_id: int = Path(le=2147483647, ge=1),  # чтобы не было 500 ошибки при больших или числах <0
        user_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    team = await remove_member_from_team(team_id=team_id, current_user=current_user, user_id=user_id, db=db)
    if team is None:
        raise HTTPException(status_code=404, detail=f'Команды с id:{team_id} не существует')

    if team is False:
        raise HTTPException(status_code=403, detail='Недостаточно прав')
    return team


@teams_router.patch('/{team_id}/members/{user_id}/role/')
async def change_members_role(
        new_role: UpdateRoleRequest,
        team_id: int = Path(le=2147483647, ge=1),
        user_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    updated_member = await update_members_role(
        team_id=team_id,
        user_id=user_id,
        new_role=new_role.role,
        current_user=current_user,
        db=db
    )

    if not updated_member:
        raise HTTPException(
            status_code=404,
            detail='Команда не найдена, пользователя нет в списке или у вас недостаточно прав'
        )

    return updated_member


@teams_router.delete('/{team_id}/leave/')
async def leave_from_team(
        team_id: int = Path(le=2147483647, ge=1),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
):
    leaved_member = await leave_team(team_id=team_id, user_id=current_user.id, db=db)

    if not leaved_member:
        raise HTTPException(
            status_code=404,
            detail='Команда не найдена, пользователя нет в списке или у вы не состоите в этой команде'
        )

    return {'detail': 'Вы вышли из команды'}
