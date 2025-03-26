from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CommitFile")


@_attrs_define
class CommitFile:
    """
    Attributes:
        path (str): Path of the changed file
        type_ (str): Type of change (added, modified, deleted)
    """

    path: str
    type_: str

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "path": path,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        path = d.pop("path")

        type_ = d.pop("type")

        commit_file = cls(
            path=path,
            type_=type_,
        )

        return commit_file
