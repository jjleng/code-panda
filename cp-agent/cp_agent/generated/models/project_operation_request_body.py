from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectOperationRequestBody")


@_attrs_define
class ProjectOperationRequestBody:
    """
    Attributes:
        project_id (str): ID of the project
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    project_id: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        project_id = self.project_id

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "project_id": project_id,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        project_id = d.pop("project_id")

        schema = d.pop("$schema", UNSET)

        project_operation_request_body = cls(
            project_id=project_id,
            schema=schema,
        )

        return project_operation_request_body
