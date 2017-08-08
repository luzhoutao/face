from django.test import TestCase
import requests
import os
from rest_framework import status
from rest_framework.reverse import reverse

# Create your tests here.

admin_name = 'admin'
admin_password = 'password123'
'''
class CompaniesCRUDTest(TestCase):

    host = "http://127.0.0.1:8000/"

    def test_anonymous_can_create(self):
        uri = 'companies/'
        data = {'username': 'test_anonymous_can_create', 'email': 'luzhoutao@gmail.com', 'password': 'password123'}
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
'''
class PersonTest(TestCase):

    host = 'http://127.0.0.1:8000/'

    def test_anonymous_cannot_access_person(self):
        url = os.path.join(self.host, 'persons/')
        response = requests.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = requests.put(url, data={'name': 'hello'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = requests.post(url, data={'first_name': 'hello'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = requests.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_and_delete_person(self):
        user = {'username': 'test_person_user', 'email': 'test_person_user@example.com', 'password': 'password123'}
        url = os.path.join(self.host, 'companies/')
        response = requests.post(url, data=user)
        user['id'] = response.json()['id']

        url = os.path.join(self.host, 'persons/')
        person = {'name': 'test_person', 'email': 'test_person@example.com'}
        response = requests.post(url, data=person, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        person['id'] = response.json()['id']

        url = url + str(person['id']) + '/'
        response = requests.delete(url, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        url = os.path.join(self.host, 'company/'+str(user['id'])+'/')
        requests.delete(url, auth=(admin_name, admin_password))

    def test_owner_can_list_and_retrieve_person(self):
        user = {'username': 'test_person_user', 'email': 'test_person_user@example.com', 'password': 'password123'}
        url = os.path.join(self.host, 'companies/')
        response = requests.post(url, data=user)
        user['id'] = response.json()['id']

        url = os.path.join(self.host, 'persons/')
        person = {'name': 'test_person', 'email': 'test_person@example.com'}
        response = requests.post(url, data=person, auth=(user['username'], user['password']))
        person['id'] = response.json()['id']

        # list
        response = requests.get(url, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve
        url = url + str(person['id']) + '/'
        response = requests.get(url, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = os.path.join(self.host, 'company/' + str(user['id']) + '/')
        requests.delete(url, auth=(admin_name, admin_password))

    def test_owner_can_upate(self):
        user = {'username': 'test_person_user', 'email': 'test_person_user@example.com', 'password': 'password123'}
        url = os.path.join(self.host, 'companies/')
        response = requests.post(url, data=user)
        user['id'] = response.json()['id']

        url = os.path.join(self.host, 'persons/')
        person = {'name': 'test_person', 'email': 'test_person@example.com'}
        response = requests.post(url, data=person, auth=(user['username'], user['password']))
        person['id'] = response.json()['id']

        # update
        url = url + str(person['id']) + '/'
        updated_data = {'first_name': 'Firstname'}
        response = requests.put(url, data=updated_data, auth=(user['username'], user['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = os.path.join(self.host, 'company/' + str(user['id']) + '/')
        requests.delete(url, auth=(admin_name, admin_password))