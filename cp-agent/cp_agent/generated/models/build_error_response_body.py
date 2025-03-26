from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="BuildErrorResponseBody")


@_attrs_define
class BuildErrorResponseBody:
    """
    Attributes:
        build_errors (bool): Whether there were any build errors
        message (str): Build error check output message
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    build_errors: bool
    message: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        build_errors = self.build_errors

        message = self.message

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "buildErrors": build_errors,
                "message": message,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        build_errors = d.pop("buildErrors")

        message = d.pop("message")

        schema = d.pop("$schema", UNSET)

        build_error_response_body = cls(
            build_errors=build_errors,
            message=message,
            schema=schema,
        )

        return build_error_response_body
