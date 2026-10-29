"""Factory for the plain CRUD endpoints shared by most master data resources."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from django.db import models
from django.db.models import ProtectedError, QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema, Query, Router, Schema, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from apps.accounts.permissions import WRITE

from .pagination import Pagination
from .querying import order, search
from .security import AuthedRequest, it_staff_auth, permission_auth

if TYPE_CHECKING:
    # build_crud_router annotates the endpoints with the schemas of the config, from
    # which Ninja builds the API; they are bound only at runtime, so the type checker
    # sees their base classes.
    Out = Schema
    In = Schema
    Filter = FilterSchema


class EmptyFilter(FilterSchema):
    """Default filter: only by ids. (A filter schema without fields would become a
    required query parameter in django-ninja.)"""

    ids: Annotated[list[UUID] | None, FilterLookup("id__in")] = None


@dataclass
class CrudConfig[M: models.Model]:
    model: type[M]
    out_schema: type[Schema]
    in_schema: type[Schema]
    filter_schema: type[FilterSchema] = EmptyFilter
    search_fields: tuple[str, ...] = ()
    ordering_fields: tuple[str, ...] = ("name",)
    queryset: Callable[[], QuerySet[M]] | None = None
    # Builds the unsaved record that creating fills in; by default ``model()``.
    new: Callable[[], M] | None = None
    # Hook to translate/validate the input before saving (e.g. resolving FKs).
    prepare: Callable[[dict[str, Any]], dict[str, Any]] = field(default=lambda data: data)
    # Area of the role rights (apps.accounts.permissions) that creating, changing
    # and deleting needs.
    permission: str | None = None
    # Instead of ``permission``: the auth for writing, e.g. administrators only.
    write_auth: object | None = None
    # Auth for reading; by default IT staff, since master data is IT's working material.
    read_auth: object | None = None
    # Called with the request and the existing record before it is changed or deleted;
    # raises HttpError to refuse (e.g. only administrators may change administrators).
    check_change: Callable[[AuthedRequest, M], None] | None = None
    # Called with the request, the input and the existing record (None when creating)
    # before saving; raises HttpError to refuse values the user may not set.
    check_input: Callable[[AuthedRequest, dict[str, Any], M | None], None] | None = None
    # Called with the request and the record before it is deleted; raises HttpError to refuse.
    check_delete: Callable[[AuthedRequest, M], None] | None = None

    def get_queryset(self) -> QuerySet[M]:
        return self.queryset() if self.queryset else self.model._default_manager.all()


def apply_input[M: models.Model](instance: M, data: dict[str, Any]) -> M:
    m2m: dict[str, Any] = {}
    for name, value in data.items():
        model_field = instance._meta.get_field(name)
        if model_field.many_to_many:
            m2m[name] = value
        elif model_field.is_relation:
            setattr(instance, f"{name}_id", value)
        else:
            setattr(instance, name, value)
    instance.full_clean()
    instance.save()
    for name, value in m2m.items():
        getattr(instance, name).set(value)
    return instance


def build_crud_router[M: models.Model](config: CrudConfig[M], *, tags: list[str]) -> Router:
    router = Router(tags=tags)
    write_auth = config.write_auth or (
        permission_auth(config.permission, WRITE) if config.permission else it_staff_auth
    )
    read_auth = config.read_auth or it_staff_auth
    if not TYPE_CHECKING:
        # For the annotations below, which Ninja evaluates (ruff takes them for the aliases above).
        Out, In, Filter = config.out_schema, config.in_schema, config.filter_schema  # noqa: F841

    def get_instance(pk: UUID) -> M:
        return get_object_or_404(config.get_queryset(), pk=pk)

    def get_for_change(request: AuthedRequest, pk: UUID) -> M:
        instance = get_instance(pk)
        if config.check_change:
            config.check_change(request, instance)
        return instance

    @router.get("", response=list[Out], auth=read_auth)
    @paginate(Pagination)
    def list_items(
        request: AuthedRequest,
        filters: Query[Filter],
        q: str | None = None,
        ordering: str | None = None,
    ):
        queryset = filters.filter(config.get_queryset())
        queryset = search(queryset, q, config.search_fields)
        return order(queryset, ordering, config.ordering_fields)

    @router.get("/{uuid:pk}", response=Out, auth=read_auth)
    def get_item(request: AuthedRequest, pk: UUID):
        return get_instance(pk)

    @router.post("", response={201: Out}, auth=write_auth)
    def create_item(request: AuthedRequest, payload: In):
        data = payload.dict()
        if config.check_input:
            config.check_input(request, data, None)
        new = config.new() if config.new else config.model()
        instance = apply_input(new, config.prepare(data))
        return Status(201, get_instance(instance.pk))

    @router.put("/{uuid:pk}", response=Out, auth=write_auth)
    def update_item(request: AuthedRequest, pk: UUID, payload: In):
        instance = get_for_change(request, pk)
        data = payload.dict()
        if config.check_input:
            config.check_input(request, data, instance)
        instance = apply_input(instance, config.prepare(data))
        return get_instance(instance.pk)

    @router.delete("/{uuid:pk}", response={204: None}, auth=write_auth)
    def delete_item(request: AuthedRequest, pk: UUID):
        instance = get_for_change(request, pk)
        if config.check_delete:
            config.check_delete(request, instance)
        try:
            instance.delete()
        except ProtectedError as exc:
            raise HttpError(409, _("This record is still in use and cannot be deleted.")) from exc
        return Status(204, None)

    return router
