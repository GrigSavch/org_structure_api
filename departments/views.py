import logging

from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from employees.models import Employee
from employees.serializers import EmployeeCreateSerializer

from .models import Department
from .serializers import (
    DepartmentCreateSerializer,
    DepartmentDetailSerializer,
    DepartmentUpdateSerializer,
)

logger = logging.getLogger(__name__)


class DepartmentListView(generics.ListCreateAPIView):
    """
    GET: List all departments
    POST: Create a new department
    """

    queryset = Department.objects.all()
    serializer_class = DepartmentCreateSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DepartmentCreateSerializer
        return DepartmentCreateSerializer


class DepartmentCreateView(generics.CreateAPIView):
    """Create a new department"""

    queryset = Department.objects.all()
    serializer_class = DepartmentCreateSerializer

    def perform_create(self, serializer):
        logger.info(
            f'Creating department: {serializer.validated_data.get("name")}'
        )
        serializer.save()


class DepartmentDetailView(generics.RetrieveAPIView):
    """Get department details with children and employees"""

    queryset = Department.objects.all()
    serializer_class = DepartmentDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # Get query parameters
        depth = self.request.query_params.get('depth', 1)
        include_employees = (
            self.request.query_params.get('include_employees', 'true').lower()
            == 'true'
        )
        employee_order = self.request.query_params.get(
            'employee_order', 'created_at'
        )

        # Validate depth
        try:
            depth = int(depth)
            if depth < 0:
                depth = 1
            if depth > 5:
                depth = 5
        except ValueError:
            depth = 1

        context['depth'] = depth
        context['include_employees'] = include_employees
        context['employee_order'] = (
            employee_order
            if employee_order in ['created_at', 'full_name']
            else 'created_at'
        )

        return context


class DepartmentUpdateView(generics.UpdateAPIView):
    """Update department (move to another parent)"""

    queryset = Department.objects.all()
    serializer_class = DepartmentUpdateSerializer
    http_method_names = ['patch']

    def perform_update(self, serializer):
        logger.info(f'Updating department {self.get_object().id}')
        serializer.save()


class DepartmentDeleteView(generics.DestroyAPIView):
    """Delete department with cascade or reassign options"""

    queryset = Department.objects.all()

    def destroy(self, request, *args, **kwargs):
        department = self.get_object()
        mode = request.query_params.get('mode', 'cascade')

        logger.info(f'Deleting department {department.id} with mode: {mode}')

        if mode == 'reassign':
            reassign_to_id = request.query_params.get(
                'reassign_to_department_id'
            )

            if not reassign_to_id:
                raise ValidationError(
                    'reassign_to_department_id is required when mode=reassign'
                )

            try:
                reassign_to = Department.objects.get(id=reassign_to_id)
            except Department.DoesNotExist:
                raise NotFound('Target department not found')

            with transaction.atomic():
                # Reassign employees
                Employee.objects.filter(department=department).update(
                    department=reassign_to
                )

                # Reassign child departments
                department.children.update(parent=reassign_to)

                # Delete the department
                department.delete()

        elif mode == 'cascade':
            # Cascade delete - will be handled by database
            department.delete()

        else:
            raise ValidationError(
                "mode must be either 'cascade' or 'reassign'"
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class DepartmentEmployeeCreateView(generics.CreateAPIView):
    """Create an employee in a department"""

    serializer_class = EmployeeCreateSerializer

    def create(self, request, *args, **kwargs):
        department_id = kwargs.get('dept_id')

        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            raise NotFound('Department not found')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer, department)

        logger.info(
            f'Created employee {serializer.instance.id if serializer.instance else ""} in department {department_id}'
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, department):
        serializer.save(department=department)
