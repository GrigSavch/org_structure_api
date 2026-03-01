from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Employee(models.Model):
    full_name = models.CharField(
        max_length=200, verbose_name='Полное имя', help_text='ФИО сотрудника'
    )
    position = models.CharField(
        max_length=200,
        verbose_name='Должность',
        help_text='Должность сотрудника',
    )
    hired_at = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата найма',
        help_text='Дата найма сотрудника',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name='Подразделение',
        help_text='Подразделение сотрудника',
    )

    class Meta:
        app_label = 'employees'
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['position']),
            models.Index(fields=['hired_at']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f'{self.full_name} - {self.position}'

    def clean(self):
        """Валидация модели"""
        if self.full_name:
            self.full_name = self.full_name.strip()

        if self.position:
            self.position = self.position.strip()

        if not self.full_name:
            raise ValidationError({'full_name': 'Имя не может быть пустым'})

        if not self.position:
            raise ValidationError(
                {'position': 'Должность не может быть пустой'}
            )

        if len(self.full_name) < 1 or len(self.full_name) > 200:
            raise ValidationError(
                {'full_name': 'Имя должно быть от 1 до 200 символов'}
            )

        if len(self.position) < 1 or len(self.position) > 200:
            raise ValidationError(
                {'position': 'Должность должна быть от 1 до 200 символов'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
