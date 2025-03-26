from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_diff import FileDiff


T = TypeVar("T", bound="GetFileDiffResponseBody")


@_attrs_define
class GetFileDiffResponseBody:
    """
    Attributes:
        diff (FileDiff):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    diff: "FileDiff"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        diff = self.diff.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "diff": diff,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.file_diff import FileDiff

        d = src_dict.copy()
        diff = FileDiff.from_dict(d.pop("diff"))

        schema = d.pop("$schema", UNSET)

        get_file_diff_response_body = cls(
            diff=diff,
            schema=schema,
        )

        return get_file_diff_response_body
