from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CheckPreviewResponseBody")


@_attrs_define
class CheckPreviewResponseBody:
    """
    Attributes:
        healthy (bool):
        status (int):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    healthy: bool
    status: int
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        healthy = self.healthy

        status = self.status

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "healthy": healthy,
                "status": status,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        healthy = d.pop("healthy")

        status = d.pop("status")

        schema = d.pop("$schema", UNSET)

        check_preview_response_body = cls(
            healthy=healthy,
            status=status,
            schema=schema,
        )

        return check_preview_response_body
