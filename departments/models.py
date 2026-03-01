from django.core.exceptions import ValidationError
from django.db import models


class Department(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Название подразделения',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительское подразделение',
        help_text='Родительское подразделение (null для корневого)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        app_label = 'departments'
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'parent'],
                name='unique_department_name_per_parent',
            )
        ]
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['parent']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.name:
            self.name = self.name.strip()

        if not self.name:
            raise ValidationError({'name': 'Название не может быть пустым'})

        if len(self.name) < 1 or len(self.name) > 200:
            raise ValidationError(
                {'name': 'Название должно быть от 1 до 200 символов'}
            )

        if self.parent and self.parent.pk == self.pk:
            raise ValidationError(
                {'parent': 'Подразделение не может быть родителем самого себя'}
            )

        if self.pk and self.parent:
            if self._has_cycle():
                raise ValidationError(
                    {'parent': 'В структуре подразделений есть цикл'}
                )

    def _has_cycle(self):
        if not self.parent:
            return False

        visited = set()
        current = self.parent

        while current:
            if current.pk in visited:
                return True
            if current.pk == self.pk:
                return True
            visited.add(current.pk)
            current = current.parent

        return False

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self._clean_name()

    def _clean_name(self):
        if self.name:
            self.name = self.name.strip()
