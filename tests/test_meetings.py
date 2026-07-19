import pytest

from datetime import datetime, timezone, timedelta


def get_future_dates(days_ahead=1, duration_hours=1):
    """
    Вспомогательная функция для генерации даты в строку
    """
    start = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    end = start + timedelta(hours=duration_hours)
    return start.isoformat(), end.isoformat()


@pytest.mark.asyncio
async def test_add_meeting_success(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates()

    payload = {
        'starts_at': starts_at,
        'ends_at': ends_at,
        'member_ids': []
    }

    res = await client.post(f'/teams/{team_id}/meetings/', json=payload, headers=headers)

    assert res.status_code == 200
    assert 'id' in res.json()


@pytest.mark.asyncio
async def test_add_meeting_not_manager(client, create_registered_test_user_manager, create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 1'}, headers=manager_headers)
    team_id = team_res.json()['id']
    invite_code = team_res.json()['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    starts_at, ends_at = get_future_dates()
    payload = {'starts_at': starts_at, 'ends_at': ends_at}

    res = await client.post(f'/teams/{team_id}/meetings/', json=payload, headers=member_headers)

    assert res.status_code == 403
    assert 'нет доступа' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_meeting_foreign_members(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 2'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates()

    payload = {
        'starts_at': starts_at,
        'ends_at': ends_at,
        'member_ids': [9999]
    }

    res = await client.post(f'/teams/{team_id}/meetings/', json=payload, headers=headers)

    assert res.status_code == 400
    assert 'не состоят в команде' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_meeting_past_date(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 3'}, headers=headers)
    team_id = team_res.json()['id']

    # Дата в прошлом
    starts_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    ends_at = datetime.now(timezone.utc).isoformat()

    res = await client.post(f'/teams/{team_id}/meetings/', json={'starts_at': starts_at, 'ends_at': ends_at},
                            headers=headers)

    assert res.status_code == 400
    assert 'в прошлом' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_meeting_start_after_end(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 4'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates()

    payload = {'starts_at': ends_at, 'ends_at': starts_at}

    res = await client.post(f'/teams/{team_id}/meetings/', json=payload, headers=headers)

    assert res.status_code == 400
    assert 'должно быть раньше времени окончания' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_meeting_in_past(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 5'}, headers=headers)
    team_id = team_res.json()['id']

    # Даты в прошлом
    starts_at = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    ends_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    payload = {'starts_at': starts_at, 'ends_at': ends_at}

    res = await client.post(f'/teams/{team_id}/meetings/', json=payload, headers=headers)

    assert res.status_code == 400
    assert 'в прошлом' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_add_meeting_overlap(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 6'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates(days_ahead=2)

    await client.post(f'/teams/{team_id}/meetings/', json={'starts_at': starts_at, 'ends_at': ends_at}, headers=headers)

    res = await client.post(f'/teams/{team_id}/meetings/', json={'starts_at': starts_at, 'ends_at': ends_at},
                            headers=headers)

    assert res.status_code == 403
    assert 'уже запланирована' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_list_meetings_member_only(client, create_registered_test_user_manager,
                                         create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    outsider_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 7'}, headers=manager_headers)
    team_id = team_res.json()['id']

    res = await client.get(f'/teams/{team_id}/meetings/', headers=outsider_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_update_meeting_success(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 8'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates(days_ahead=3)
    post_res = await client.post(f'/teams/{team_id}/meetings/', json={'starts_at': starts_at, 'ends_at': ends_at},
                                 headers=headers)
    meeting_id = post_res.json()['id']

    new_starts, new_ends = get_future_dates(days_ahead=4)
    patch_res = await client.patch(
        f'/teams/{team_id}/meetings/{meeting_id}/',
        json={'starts_at': new_starts, 'ends_at': new_ends},
        headers=headers
    )

    assert patch_res.status_code == 200
    # Убрал 16 символов, т.к. милисекунды могут отличаться
    assert patch_res.json()['starts_at'].startswith(new_starts[:16])


@pytest.mark.asyncio
async def test_delete_meeting_success(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Meet Team 9'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates(days_ahead=5)
    post_res = await client.post(f'/teams/{team_id}/meetings/', json={'starts_at': starts_at, 'ends_at': ends_at},
                                 headers=headers)
    meeting_id = post_res.json()['id']

    del_res = await client.delete(f'/teams/{team_id}/meetings/{meeting_id}/', headers=headers)
    assert del_res.status_code == 200

    get_res = await client.get(f'/teams/{team_id}/meetings/', headers=headers)
    assert len(get_res.json()) == 0


@pytest.mark.asyncio
async def test_calendar_success(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    from_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

    res = await client.get(f'/teams/calendar/?from={from_date}&to={to_date}', headers=headers)

    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_calendar_invalid_range(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }

    # Неправильный диапазон
    from_date = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
    to_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    res = await client.get(f'/teams/calendar/?from={from_date}&to={to_date}', headers=headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_update_meeting_not_found(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Update Meet Team'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates()

    res = await client.patch(
        f'/teams/{team_id}/meetings/9999/',
        json={'starts_at': starts_at, 'ends_at': ends_at},
        headers=headers
    )

    assert res.status_code == 404
    assert 'не найдена' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_update_meeting_not_manager(client, create_registered_test_user_manager,
                                          create_registered_test_user_member):
    manager_headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    member_headers = {
        'Authorization': f'Bearer {create_registered_test_user_member}'
    }

    team_res = await client.post('/teams/create_team/', json={'name': 'Update Meet Team 1'}, headers=manager_headers)
    team_id = team_res.json()['id']
    invite_code = team_res.json()['invite_code']

    await client.post(f'/teams/{invite_code}/join/', headers=member_headers)

    starts_at, ends_at = get_future_dates(days_ahead=2)
    meet_res = await client.post(
        f'/teams/{team_id}/meetings/',
        json={'starts_at': starts_at, 'ends_at': ends_at},
        headers=manager_headers
    )
    meeting_id = meet_res.json()['id']

    new_starts, new_ends = get_future_dates(days_ahead=3)
    res = await client.patch(
        f'/teams/{team_id}/meetings/{meeting_id}/',
        json={'starts_at': new_starts, 'ends_at': new_ends},
        headers=member_headers
    )

    assert res.status_code == 403
    assert 'нет доступа' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_update_meeting_not_found(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Update Meet Team 2'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates()

    res = await client.patch(
        f'/teams/{team_id}/meetings/9999/',
        json={'starts_at': starts_at, 'ends_at': ends_at},
        headers=headers
    )

    assert res.status_code == 404
    assert 'не найдена' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_update_meeting_start_after_end(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Update Meet Team 3'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates(days_ahead=4)
    meet_res = await client.post(
        f'/teams/{team_id}/meetings/',
        json={'starts_at': starts_at, 'ends_at': ends_at},
        headers=headers
    )
    meeting_id = meet_res.json()['id']

    res = await client.patch(
        f'/teams/{team_id}/meetings/{meeting_id}/',
        json={'starts_at': ends_at, 'ends_at': starts_at},
        headers=headers
    )

    assert res.status_code == 400
    assert 'должно быть раньше времени окончания' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_update_meeting_in_past(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Update Meet Team 4'}, headers=headers)
    team_id = team_res.json()['id']

    starts_at, ends_at = get_future_dates(days_ahead=5)
    meet_res = await client.post(
        f'/teams/{team_id}/meetings/',
        json={'starts_at': starts_at, 'ends_at': ends_at},
        headers=headers
    )
    meeting_id = meet_res.json()['id']

    past_start = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    past_end = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    res = await client.patch(
        f'/teams/{team_id}/meetings/{meeting_id}/',
        json={'starts_at': past_start, 'ends_at': past_end},
        headers=headers
    )

    assert res.status_code == 400
    assert 'в прошлом' in res.json()['detail'].lower()


@pytest.mark.asyncio
async def test_update_meeting_overlap(client, create_registered_test_user_manager):
    headers = {
        'Authorization': f'Bearer {create_registered_test_user_manager}'
    }
    team_res = await client.post('/teams/create_team/', json={'name': 'Update Meet Team 5'}, headers=headers)
    team_id = team_res.json()['id']

    start_1, end_1 = get_future_dates(days_ahead=6)
    await client.post(
        f'/teams/{team_id}/meetings/',
        json={'starts_at': start_1, 'ends_at': end_1},
        headers=headers
    )

    start_2, end_2 = get_future_dates(days_ahead=7)
    meet_res_2 = await client.post(
        f'/teams/{team_id}/meetings/',
        json={'starts_at': start_2, 'ends_at': end_2},
        headers=headers
    )
    meeting_id_2 = meet_res_2.json()['id']

    res = await client.patch(
        f'/teams/{team_id}/meetings/{meeting_id_2}/',
        json={'starts_at': start_1, 'ends_at': end_1},
        headers=headers
    )

    assert res.status_code == 403
    assert 'уже запланирована' in res.json()['detail'].lower()
