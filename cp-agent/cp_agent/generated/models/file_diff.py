from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="FileDiff")


@_attrs_define
class FileDiff:
    """
    Attributes:
        new_text (str): Modified content of the file
        old_text (str): Original content of the file
        path (str): Path of the file
    """

    new_text: str
    old_text: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        new_text = self.new_text

        old_text = self.old_text

        path = self.path

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "new_text": new_text,
                "old_text": old_text,
                "path": path,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        new_text = d.pop("new_text")

        old_text = d.pop("old_text")

        path = d.pop("path")

        file_diff = cls(
            new_text=new_text,
            old_text=old_text,
            path=path,
        )

        return file_diff
