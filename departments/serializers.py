import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from employees.serializers import EmployeeSerializer

from .models import Department

logger = logging.getLogger(__name__)


class DepartmentBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = ['id', 'name', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        if value:
            value = value.strip()
        if not value:
            raise serializers.ValidationError('Название не может быть пустым')
        return value

    def validate_parent(self, value):
        if value and self.instance:
            if value.id == self.instance.id:
                raise serializers.ValidationError(
                    'Подразделение не может быть родителем самого себя'
                )
        return value

    def validate(self, data):
        name = data.get('name', getattr(self.instance, 'name', None))
        parent = data.get('parent', getattr(self.instance, 'parent', None))

        if name and parent is not None:
            queryset = Department.objects.filter(name=name, parent=parent)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        'name': (
                            'Подразделение с таким именем '
                            'уже существует в этом родителе'
                        )
                    }
                )

        if self.instance and 'parent' in data:
            new_parent = data['parent']
            if new_parent:
                if self._would_create_cycle(self.instance, new_parent):
                    raise serializers.ValidationError(
                        {
                            'parent': (
                                'Невозможно переместить: '
                                'это создаст цикл в иерархии'
                            )
                        }
                    )

        return data

    def _would_create_cycle(self, department, new_parent):
        if not new_parent:
            return False

        visited = set()
        current = new_parent

        while current:
            if current.pk in visited:
                return True
            if current.pk == department.pk:
                return True
            visited.add(current.pk)
            current = current.parent

        return False


class DepartmentCreateSerializer(DepartmentBaseSerializer):

    class Meta(DepartmentBaseSerializer.Meta):
        fields = DepartmentBaseSerializer.Meta.fields

    def create(self, validated_data):
        try:
            department = Department.objects.create(**validated_data)
            logger.info(
                f'Created department: {department.name} (ID: {department.id})'
            )
            return department
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class DepartmentUpdateSerializer(DepartmentBaseSerializer):

    class Meta(DepartmentBaseSerializer.Meta):
        fields = DepartmentBaseSerializer.Meta.fields

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()
                logger.info(
                    f'Updated department: {instance.name} (ID: {instance.id})'
                )
                return instance
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class DepartmentDetailSerializer(serializers.ModelSerializer):

    employees = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'parent',
            'created_at',
            'employees',
            'children',
        ]

    def get_employees(self, obj):
        include_employees = self.context.get('include_employees', True)
        if not include_employees:
            return []

        employees = obj.employees.all()
        sort_by = self.context.get('sort_employees_by', 'created_at')

        if sort_by == 'full_name':
            employees = employees.order_by('full_name')
        else:
            employees = employees.order_by('-created_at')

        return EmployeeSerializer(employees, many=True).data

    def get_children(self, obj):
        depth = self.context.get('depth', 1)
        current_depth = self.context.get('current_depth', 0)

        if current_depth >= depth or depth <= 0:
            return []

        children = obj.children.all()

        serializer = DepartmentDetailSerializer(
            children,
            many=True,
            context={
                **self.context,
                'current_depth': current_depth + 1,
                'include_employees': False,
            },
        )

        return serializer.data


class DepartmentDeleteSerializer(serializers.Serializer):

    MODE_CHOICES = [('cascade', 'Cascade'), ('reassign', 'Reassign')]

    mode = serializers.ChoiceField(
        choices=MODE_CHOICES,
        required=True,
        help_text='Режим удаления: cascadeили reassign',
    )
    reassign_to_department_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=(
            'ID подразделения для переназначения '
            'сотрудников (обязателен при mode=reassign)'
        ),
    )

    def validate(self, data):
        mode = data.get('mode')
        reassign_to_id = data.get('reassign_to_department_id')

        if mode == 'reassign' and not reassign_to_id:
            raise serializers.ValidationError(
                'reassign_to_department_id обязателен при mode=reassign'
            )

        if mode == 'reassign' and reassign_to_id:
            try:
                department = Department.objects.get(pk=reassign_to_id)
                if (
                    hasattr(self, 'instance')
                    and self.instance
                    and department.pk == self.instance.pk
                ):
                    raise serializers.ValidationError(
                        (
                            'Нельзя переназначить сотрудников '
                            'в удаляемое подразделение'
                        )
                    )
            except Department.DoesNotExist:
                raise serializers.ValidationError(
                    f'Подразделение с ID {reassign_to_id} не существует'
                )

        return data
