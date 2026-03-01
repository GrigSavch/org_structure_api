from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from employees.models import Employee

from .models import Department


class DepartmentModelTests(TestCase):
    def test_create_department(self):
        department = Department.objects.create(name='IT Department')
        self.assertEqual(department.name, 'IT Department')
        self.assertIsNone(department.parent)

    def test_unique_name_per_parent(self):
        parent = Department.objects.create(name='Parent')
        Department.objects.create(name='Child', parent=parent)

        with self.assertRaises(IntegrityError):
            Department.objects.create(name='Child', parent=parent)

    def test_circular_reference_prevention(self):
        dept1 = Department.objects.create(name='Dept1')
        dept2 = Department.objects.create(name='Dept2', parent=dept1)

        dept1.parent = dept2
        with self.assertRaises(ValidationError):
            dept1.save()


class DepartmentAPITests(APITestCase):
    def setUp(self):
        self.department_data = {'name': 'IT Department'}

    def test_create_department(self):
        url = reverse('department-create')
        response = self.client.post(url, self.department_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'IT Department')
        self.assertIsNotNone(response.data['id'])

    def test_create_department_with_parent(self):
        parent = Department.objects.create(name='Parent')
        data = {'name': 'Child', 'parent': parent.id}

        url = reverse('department-create')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent.id)

    def test_create_employee_in_department(self):
        department = Department.objects.create(name='IT')
        url = reverse('department-employee-create', args=[department.id])

        employee_data = {
            'full_name': 'Иван Иванов',
            'position': 'Developer',
            'hired_at': '2023-01-01',
        }

        response = self.client.post(url, employee_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['full_name'], 'Иван Иванов')

        self.assertTrue(
            Employee.objects.filter(full_name='Иван Иванов').exists()
        )
