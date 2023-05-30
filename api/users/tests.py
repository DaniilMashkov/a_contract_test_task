from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from rest_framework.test import APIClient

TEST_PASSWORD = 'test_pass'


@pytest.fixture
def user_with_password(user: 'User'):
    user.set_password(TEST_PASSWORD)
    user.save()
    return user


@pytest.mark.django_db
def test_auth_using_login_pass(anon_client: 'APIClient', user_with_password: 'User'):
    username = user_with_password.username
    response = anon_client.post(
        '/api/auth/login/',
        data={'username': username, 'password': 'incorrect_password'},
    )
    assert response.status_code == 403

    response = anon_client.post(
        '/api/auth/login/', data={'username': username, 'password': TEST_PASSWORD}
    )
    assert response.status_code == 200, response.content

    data = response.json()

    assert data['username'] == username


@pytest.mark.django_db
def test_user_flow(admin_client: 'APIClient', anon_client: 'APIClient'):
    users_count = 20
    users_data = [
        {
            'username': f'user_{i}',
            'password': f'password_{i}',
            'email': f'email_{i}@mail.ru',
        }
        for i in range(users_count)
    ]

    """ Создаем пользователей"""
    for user in users_data:
        response = admin_client.post(
            '/api/v1/users/',
            data=user
        )
        user['id'] = response.data.get('id')
        assert response.status_code == 201

    """ Проверяем количество созданных пользователей """
    response = admin_client.get('/api/v1/users/')
    assert response.data.get('count') == users_count
    assert response.status_code == 200

    """ Проверяем возможность авторизации для каждого пользователя """
    for user in users_data:
        response = anon_client.post(
            '/api/auth/login/', data={**user}
        )
        assert response.status_code == 200, response.content

    """ Удаляем созданных пользователей """
    for user in users_data:
        response = admin_client.delete(f'/api/v1/users/{user["id"]}/')
        assert response.status_code == 204
