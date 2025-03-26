from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="FileNode")


@_attrs_define
class FileNode:
    """
    Attributes:
        name (str): Name of the file or directory
        type_ (str): Type of the node (file or folder)
        children (Union[None, Unset, list['FileNode']]): Child nodes for directories
    """

    name: str
    type_: str
    children: Union[None, Unset, list["FileNode"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_

        children: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.children, Unset):
            children = UNSET
        elif isinstance(self.children, list):
            children = []
            for children_type_0_item_data in self.children:
                children_type_0_item = children_type_0_item_data.to_dict()
                children.append(children_type_0_item)

        else:
            children = self.children

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "type": type_,
            }
        )
        if children is not UNSET:
            field_dict["children"] = children

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        type_ = d.pop("type")

        def _parse_children(data: object) -> Union[None, Unset, list["FileNode"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                children_type_0 = []
                _children_type_0 = data
                for children_type_0_item_data in _children_type_0:
                    children_type_0_item = FileNode.from_dict(children_type_0_item_data)

                    children_type_0.append(children_type_0_item)

                return children_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["FileNode"]], data)

        children = _parse_children(d.pop("children", UNSET))

        file_node = cls(
            name=name,
            type_=type_,
            children=children,
        )

        return file_node
