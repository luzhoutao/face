from django.test import TestCase
import requests
import os
from rest_framework import status
from rest_framework.reverse import reverse

# Create your tests here.

admin_name = 'admin'
admin_password = 'password123'

class CompaniesCRUDTest(TestCase):

    host = "http://127.0.0.1:8000/"

    def test_anonymous_can_create(self):
        uri = 'companies/'
        data = {'username': 'luzhoutao', 'email': 'luzhoutao@gmail.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, uri), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_id = response.json()['id']

        # delete the inserted object
        requests.delete(os.path.join(self.host, 'company', str(new_id)), auth=('admin', 'password123'))

    def test_anonymous_cannot_list(self):
        uri = 'companies/'
        response = requests.get(os.path.join(self.host, uri))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_retrieve(self):
        uri = 'company/1/'
        response = requests.get(os.path.join(self.host, uri))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_update(self):
        uri = 'company/1/'
        data = {'email': 'changed@example.com'}
        response = requests.put(os.path.join(self.host, uri), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_delete(self):
        uri = 'company/1/'
        response = requests.delete(os.path.join(self.host, uri))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_and_delete(self):
        uri = 'companies/'
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, uri), data=data, auth=(admin_name, admin_password))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        id = response.json()['id']
        uri = 'company/' + str(id)+'/'
        response = requests.delete(os.path.join(self.host, uri), auth=(admin_name, admin_password))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_list(self):
        uri = 'companies/'
        response = requests.get(os.path.join(self.host, uri), auth=(admin_name, admin_password))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_retrieve(self):
        uri = 'company/2/'
        response = requests.get(os.path.join(self.host, uri), auth=(admin_name, admin_password))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_cannot_update(self):
        uri = 'company/2/update_info/'
        data = {'email': 'changed@example.com'}
        response = requests.put(os.path.join(self.host, uri), auth=(admin_name, admin_password), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_owner_cannot_retrieve(self):
        user1 = {'username': 'test1', 'email': 'test1@example.com', 'password': 'password123'}
        user2 = {'username': 'test2', 'email': 'test2@example.com', 'password': 'password123'}

        response = requests.post(os.path.join(self.host, 'companies/'), data=user1)
        user1['id'] = response.json()['id']
        response = requests.post(os.path.join(self.host, 'companies/'), data=user2)
        user2['id'] = response.json()['id']

        uri = 'company/'+str(user1['id'])
        response = requests.get(os.path.join(self.host, uri), auth=(user2['username'], user2['password']))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        requests.delete(os.path.join(self.host, 'company/', str(user1['id'])+'/'), auth=(admin_name, admin_password))
        requests.delete(os.path.join(self.host, 'company/', str(user2['id'])+'/'), auth=(admin_name, admin_password))

    def test_not_owner_cannot_update(self):
        user1 = {'username': 'test1', 'email': 'test1@example.com', 'password': 'password123'}
        user2 = {'username': 'test2', 'email': 'test2@example.com', 'password': 'password123'}

        response = requests.post(os.path.join(self.host, 'companies/'), data=user1)
        user1['id'] = response.json()['id']
        response = requests.post(os.path.join(self.host, 'companies/'), data=user2)
        user2['id'] = response.json()['id']

        uri = 'company/' + str(user1['id'])+'/update_info/'
        data = {'email': 'changed@example.com'}
        response = requests.put(os.path.join(self.host, uri), data=data, auth=(user2['username'], user2['password']))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        requests.delete(os.path.join(self.host, 'company/', str(user1['id'])+'/'), auth=(admin_name, admin_password))
        requests.delete(os.path.join(self.host, 'company/', str(user2['id'])+'/'), auth=(admin_name, admin_password))

    def test_owner_cannot_list(self):
        user = {'username': 'test1', 'email': 'test1@example.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, 'companies/'), data=user)
        user['id'] = response.json()['id']

        uri = 'companies/'
        response = requests.get(os.path.join(self.host, uri), auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        requests.delete(os.path.join(self.host, 'company/', str(user['id'])+'/'), auth=(admin_name, admin_password))

    def test_owner_can_create_but_cannot_delete(self):
        user = {'username': 'test1', 'email': 'test1@example.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, 'companies/'), data=user)
        user['id'] = response.json()['id']

        uri = 'companies/'
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, uri), data=data, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        id = response.json()['id']
        uri = 'company/' + str(id)+'/'
        response = requests.delete(os.path.join(self.host, uri), auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        requests.delete(os.path.join(self.host, uri), auth=(admin_name,admin_password))
        requests.delete(os.path.join(self.host, 'company/', str(user['id'])+'/'), auth=(admin_name, admin_password))

    def test_owner_can_retrieve(self):
        user = {'username': 'test1', 'email': 'test1@example.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, 'companies/'), data=user)
        user['id'] = response.json()['id']

        response = requests.get(os.path.join(self.host, 'company', str(user['id'])), auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        requests.delete(os.path.join(self.host, 'company/', str(user['id']) + '/'), auth=(admin_name, admin_password))


    def test_owner_can_update(self):
        user = {'username': 'testx', 'email': 'test1@example.com', 'password': 'password123'}
        response = requests.post(os.path.join(self.host, 'companies/'), data=user)
        user['id'] = response.json()['id']

        uri = 'company/' + str(user['id']) + '/update_info/'
        data = {'email': 'changed@example.com'}
        response = requests.put(os.path.join(self.host, uri), data=data, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        requests.delete(os.path.join(self.host, 'company/', str(user['id']) + '/'), auth=(admin_name, admin_password))