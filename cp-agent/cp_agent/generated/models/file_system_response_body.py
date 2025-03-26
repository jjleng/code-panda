from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_node import FileNode


T = TypeVar("T", bound="FileSystemResponseBody")


@_attrs_define
class FileSystemResponseBody:
    """
    Attributes:
        root (FileNode):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    root: "FileNode"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        root = self.root.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "root": root,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.file_node import FileNode

        d = src_dict.copy()
        root = FileNode.from_dict(d.pop("root"))

        schema = d.pop("$schema", UNSET)

        file_system_response_body = cls(
            root=root,
            schema=schema,
        )

        return file_system_response_body
