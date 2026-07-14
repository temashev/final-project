import pytest


@pytest.mark.asyncio
async def test_register_team_by_member(client, create_registered_test_user_member):
    payload = {
        'name': 'Test team 1',
        'invite_code': 'test_code_1'
    }

    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.post('/teams/create_team/', json=payload, headers=headers)

    assert response.status_code == 403
    assert response.json()['detail'] == 'У вас недостаточно прав'


@pytest.mark.asyncio
async def test_register_team_by_manager(client, create_registered_test_user_manager):
    payload = {
        'name': 'Test team 1',
    }

    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    response = await client.post('/teams/create_team/', json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()['name'] == 'Test team 1'


@pytest.mark.asyncio
async def test_join_by_invite_code(client, create_registered_test_user_manager, create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team = await client.post('/teams/create_team/', json={'name': 'Test team 1'}, headers=manager_headers)
    assert team.status_code == 200

    invite_code = team.json()['invite_code']

    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.post(f'/teams/{invite_code}/join/', headers=member_headers)
    assert response.status_code == 200
    assert response.json() is not None
