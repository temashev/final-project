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
async def test_add_task_user_not_in_team(client, create_registered_test_user_manager,
                                         create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    outsider_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post(
        '/teams/create_team/',
        json={'name': 'Private Task Team'},
        headers=manager_headers
    )
    team_id = team_res.json()['id']

    payload = {
        'title': 'Задача',
        'description': 'Задача в чужой команде',
        'due_date': '2026-12-31'
    }

    response = await client.post(f'/teams/{team_id}/tasks/', json=payload, headers=outsider_headers)

    assert response.status_code == 403
    assert 'нет доступа' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_get_task_user_not_in_team(client, create_registered_test_user_manager,
                                         create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    outsider_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post(
        '/teams/create_team/',
        json={'name': 'Private Task Team'},
        headers=manager_headers
    )
    team_id = team_res.json()['id']

    response = await client.get(f'/teams/{team_id}/tasks/', headers=outsider_headers)

    assert response.status_code == 403
    assert 'нет доступа' in response.json()['detail'].lower()

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


@pytest.mark.asyncio
async def test_add_evaluation_task_not_found(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Eval Team'}, headers=headers)
    team_id = team_res.json()['id']

    payload = {
        'score': 5,
        'comment': 'Good job'
    }

    response = await client.post(
        f'/teams/{team_id}/tasks/9999/evaluation',
        json=payload,
        headers=headers
    )

    assert response.status_code == 404
    assert 'не найдена' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_outsider_cannot_access_tasks(client, create_registered_test_user_member, test_team_with_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    response = await client.get(f'/teams/{test_team_with_manager.id}/tasks/', headers=headers)

    assert response.status_code == 403
    assert response.json()['detail'] == 'У вас нет доступа к задачам команды'


@pytest.mark.asyncio
async def test_member_cannot_add_evaluation(client, create_registered_test_user_member, test_team_with_member):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }
    payload = {
        'score': 5,
        'comment': 'Nice'
    }

    response = await client.post(
        f'/teams/{test_team_with_member.id}/tasks/1/evaluation',
        json=payload,
        headers=headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_member_cannot_delete_foreign_task(client, create_registered_test_user_manager,
                                                 create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Task Team'}, headers=manager_headers)
    team_id = team_res.json()['id']
    invite_code = team_res.json()['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    task_payload = {
        'title': 'Неприкосновенная задача',
        'description': 'Только для менеджера',
        'due_date': '2026-12-31'
    }
    task_res = await client.post(f'/teams/{team_id}/tasks/', json=task_payload, headers=manager_headers)
    task_id = task_res.json()['id']

    del_res = await client.delete(f'/teams/{team_id}/tasks/{task_id}', headers=member_headers)

    assert del_res.status_code == 403
    assert 'создатель или менеджер' in del_res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_comment_success(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Comment Team'}, headers=headers)
    team_id = team_res.json()['id']

    task_payload = {
        'title': 'Задача для комментов',
        'description': 'Будем писать сюда',
        'due_date': '2026-12-31'
    }
    task_res = await client.post(f'/teams/{team_id}/tasks/', json=task_payload, headers=headers)
    task_id = task_res.json()['id']

    comment_payload = {
        'text': 'Это мой первый комментарий!'
    }
    comment_res = await client.post(
        f'/teams/{team_id}/tasks/{task_id}/comments',
        json=comment_payload,
        headers=headers
    )

    assert comment_res.status_code == 200
    assert comment_res.json()['text'] == 'Это мой первый комментарий!'


@pytest.mark.asyncio
async def test_add_comment_task_not_found(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Ghost Task Team'}, headers=headers)
    team_id = team_res.json()['id']

    comment_payload = {
        'text': 'Коммент в пустоту'
    }
    comment_res = await client.post(
        f'/teams/{team_id}/tasks/9999/comments',
        json=comment_payload,
        headers=headers
    )

    assert comment_res.status_code == 404
    assert 'не найдена' in comment_res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_evaluation_success(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Eval Team Success'}, headers=headers)
    team_id = team_res.json()['id']

    task_payload = {
        'title': 'Выполненная задача',
        'description': 'Нужна оценка',
        'due_date': '2026-12-31'
    }
    task_res = await client.post(f'/teams/{team_id}/tasks/', json=task_payload, headers=headers)
    task_id = task_res.json()['id']

    await client.patch(f'/teams/{team_id}/tasks/{task_id}', json={'status': 'done'}, headers=headers)

    eval_payload = {
        'score': 5,
        'comment': 'Отличная работа!'
    }
    eval_res = await client.post(f'/teams/{team_id}/tasks/{task_id}/evaluation', json=eval_payload, headers=headers)

    assert eval_res.status_code == 200
    assert eval_res.json()['score'] == 5


@pytest.mark.asyncio
async def test_add_evaluation_task_not_done(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Eval Team Not Done'}, headers=headers)
    team_id = team_res.json()['id']

    task_payload = {
        'title': 'Задача в процессе',
        'description': 'Еще не готово',
        'due_date': '2026-12-31'
    }
    task_res = await client.post(f'/teams/{team_id}/tasks/', json=task_payload, headers=headers)
    task_id = task_res.json()['id']

    eval_payload = {
        'score': 5,
        'comment': 'Пытаюсь оценить заранее'
    }
    eval_res = await client.post(f'/teams/{team_id}/tasks/{task_id}/evaluation', json=eval_payload, headers=headers)

    assert eval_res.status_code == 403
    assert 'еще не закрыта' in eval_res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_member_cannot_update_foreign_task(client, create_registered_test_user_manager,
                                                 create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Update Team'}, headers=manager_headers)
    team_id = team_res.json()['id']
    await client.post(f'/teams/{team_res.json()["invite_code"]}/join/', headers=member_headers)

    task_res = await client.post(f'/teams/{team_id}/tasks/',
                                 json={
                                     'title': 'Task',
                                     'description': 'Описание',
                                     'due_date': '2026-12-31'
                                 },
                                 headers=manager_headers
                                 )

    task_id = task_res.json()['id']

    resp = await client.patch(f'/teams/{team_id}/tasks/{task_id}', json={'title': 'Hacked!'}, headers=member_headers)

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_nonexistent_task(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'NoTask Team'}, headers=headers)
    team_id = team_res.json()['id']

    resp = await client.patch(f'/teams/{team_id}/tasks/9999', json={'title': 'Ghost'}, headers=headers)

    assert resp.status_code == 404
