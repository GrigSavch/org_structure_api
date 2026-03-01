import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Employee

logger = logging.getLogger(__name__)


class EmployeeBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = [
            'id',
            'full_name',
            'position',
            'hired_at',
            'created_at',
            'department',
        ]
        read_only_fields = ['id', 'created_at']


class EmployeeCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = ['id', 'full_name', 'position', 'hired_at', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_full_name(self, value):
        if value:
            value = value.strip()
        if not value:
            raise serializers.ValidationError('Имя не может быть пустым')
        if len(value) > 200:
            raise serializers.ValidationError(
                'Имя не может быть длиннее 200 символов'
            )
        return value

    def validate_position(self, value):
        if value:
            value = value.strip()
        if not value:
            raise serializers.ValidationError('Должность не может быть пустой')
        if len(value) > 200:
            raise serializers.ValidationError(
                'Должность не может быть длиннее 200 символов'
            )
        return value

    def create(self, validated_data):
        try:
            employee = Employee.objects.create(**validated_data)
            logger.info(f'Created employee: {employee.full_name}')
            return employee
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = ['id', 'full_name', 'position', 'hired_at', 'created_at']
        read_only_fields = ['id', 'created_at']
