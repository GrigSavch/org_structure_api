from django.urls import path

from .views import (
    DepartmentDeleteView,
    DepartmentDetailView,
    DepartmentEmployeeCreateView,
    DepartmentListView,
    DepartmentUpdateView,
)

urlpatterns = [
    # GET /api/departments/ - список всех departments
    # POST /api/departments/ - создание нового department
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    # GET /api/departments/<pk>/ - детали department
    path(
        'departments/<int:pk>/',
        DepartmentDetailView.as_view(),
        name='department-detail',
    ),
    # PATCH /api/departments/<pk>/update/ - обновление department
    path(
        'departments/<int:pk>/update/',
        DepartmentUpdateView.as_view(),
        name='department-update',
    ),
    # DELETE /api/departments/<pk>/delete/ - удаление department
    path(
        'departments/<int:pk>/delete/',
        DepartmentDeleteView.as_view(),
        name='department-delete',
    ),
    # POST /api/departments/<dept_id>/employees/ - создание сотрудника
    path(
        'departments/<int:dept_id>/employees/',
        DepartmentEmployeeCreateView.as_view(),
        name='department-employee-create',
    ),
]
