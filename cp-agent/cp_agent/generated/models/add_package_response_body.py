from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddPackageResponseBody")


@_attrs_define
class AddPackageResponseBody:
    """
    Attributes:
        message (str): Installation output or error message
        success (bool): Whether the package installation was successful
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    message: str
    success: bool
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        success = self.success

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "message": message,
                "success": success,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        message = d.pop("message")

        success = d.pop("success")

        schema = d.pop("$schema", UNSET)

        add_package_response_body = cls(
            message=message,
            success=success,
            schema=schema,
        )

        return add_package_response_body
