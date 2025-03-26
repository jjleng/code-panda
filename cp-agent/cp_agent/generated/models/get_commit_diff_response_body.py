from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_diff import FileDiff


T = TypeVar("T", bound="GetCommitDiffResponseBody")


@_attrs_define
class GetCommitDiffResponseBody:
    """
    Attributes:
        changes (Union[None, list['FileDiff']]): List of file changes
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    changes: Union[None, list["FileDiff"]]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        changes: Union[None, list[dict[str, Any]]]
        if isinstance(self.changes, list):
            changes = []
            for changes_type_0_item_data in self.changes:
                changes_type_0_item = changes_type_0_item_data.to_dict()
                changes.append(changes_type_0_item)

        else:
            changes = self.changes

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "changes": changes,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.file_diff import FileDiff

        d = src_dict.copy()

        def _parse_changes(data: object) -> Union[None, list["FileDiff"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                changes_type_0 = []
                _changes_type_0 = data
                for changes_type_0_item_data in _changes_type_0:
                    changes_type_0_item = FileDiff.from_dict(changes_type_0_item_data)

                    changes_type_0.append(changes_type_0_item)

                return changes_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["FileDiff"]], data)

        changes = _parse_changes(d.pop("changes"))

        schema = d.pop("$schema", UNSET)

        get_commit_diff_response_body = cls(
            changes=changes,
            schema=schema,
        )

        return get_commit_diff_response_body
