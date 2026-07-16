import pytest


@pytest.mark.asyncio
async def test_add_task(client, create_registered_test_user_manager, test_team_with_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    payload = {
        'title': 'Написать тесты',
        'description': 'Покрыть CRUD задач автотестами',
        'due_date': '2026-12-31',
        'user_id': 1
    }

    response = await client.post(f'/teams/{test_team_with_manager.id}/tasks/', json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()['title'] == 'Написать тесты'
    assert 'id' in response.json()


@pytest.mark.asyncio
async def test_list_tasks(client, create_registered_test_user_member, test_team_with_member):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.get(f'/teams/{test_team_with_member.id}/tasks/', headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_task(client, create_registered_test_user_manager, test_team_with_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    payload = {
        'status': 'In progress'
    }

    response = await client.patch(f'/teams/{test_team_with_manager.id}/tasks/1', json=payload, headers=headers)

    print(response.json())
    if response.status_code == 200:
        assert response.json()['status'] == 'In progress'
    else:
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(client, create_registered_test_user_member, test_team_with_member):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.delete(f'/teams/{test_team_with_member.id}/tasks/1', headers=headers)

    if response.status_code == 200:
        assert response.json()['detail'] == 'Задача успешно удалена'
    else:
        assert response.status_code == 404
