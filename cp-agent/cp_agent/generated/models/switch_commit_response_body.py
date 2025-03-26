from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="SwitchCommitResponseBody")


@_attrs_define
class SwitchCommitResponseBody:
    """
    Attributes:
        message (str): Operation result message
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    message: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "message": message,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        message = d.pop("message")

        schema = d.pop("$schema", UNSET)

        switch_commit_response_body = cls(
            message=message,
            schema=schema,
        )

        return switch_commit_response_body
