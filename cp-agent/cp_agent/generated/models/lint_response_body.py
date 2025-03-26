from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="LintResponseBody")


@_attrs_define
class LintResponseBody:
    """
    Attributes:
        lint_errors (bool): Whether there were any lint errors
        message (str): Linting output message
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    lint_errors: bool
    message: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        lint_errors = self.lint_errors

        message = self.message

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "lintErrors": lint_errors,
                "message": message,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        lint_errors = d.pop("lintErrors")

        message = d.pop("message")

        schema = d.pop("$schema", UNSET)

        lint_response_body = cls(
            lint_errors=lint_errors,
            message=message,
            schema=schema,
        )

        return lint_response_body
