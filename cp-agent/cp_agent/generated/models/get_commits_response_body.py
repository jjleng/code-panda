from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.commit import Commit


T = TypeVar("T", bound="GetCommitsResponseBody")


@_attrs_define
class GetCommitsResponseBody:
    """
    Attributes:
        commits (Union[None, list['Commit']]): List of commits
        has_next_page (bool): Whether there are more commits available
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
        next_cursor (Union[Unset, str]): Cursor for the next page
    """

    commits: Union[None, list["Commit"]]
    has_next_page: bool
    schema: Union[Unset, str] = UNSET
    next_cursor: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        commits: Union[None, list[dict[str, Any]]]
        if isinstance(self.commits, list):
            commits = []
            for commits_type_0_item_data in self.commits:
                commits_type_0_item = commits_type_0_item_data.to_dict()
                commits.append(commits_type_0_item)

        else:
            commits = self.commits

        has_next_page = self.has_next_page

        schema = self.schema

        next_cursor = self.next_cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "commits": commits,
                "has_next_page": has_next_page,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if next_cursor is not UNSET:
            field_dict["next_cursor"] = next_cursor

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.commit import Commit

        d = src_dict.copy()

        def _parse_commits(data: object) -> Union[None, list["Commit"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                commits_type_0 = []
                _commits_type_0 = data
                for commits_type_0_item_data in _commits_type_0:
                    commits_type_0_item = Commit.from_dict(commits_type_0_item_data)

                    commits_type_0.append(commits_type_0_item)

                return commits_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["Commit"]], data)

        commits = _parse_commits(d.pop("commits"))

        has_next_page = d.pop("has_next_page")

        schema = d.pop("$schema", UNSET)

        next_cursor = d.pop("next_cursor", UNSET)

        get_commits_response_body = cls(
            commits=commits,
            has_next_page=has_next_page,
            schema=schema,
            next_cursor=next_cursor,
        )

        return get_commits_response_body
