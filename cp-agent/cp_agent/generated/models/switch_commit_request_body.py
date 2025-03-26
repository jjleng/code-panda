from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="SwitchCommitRequestBody")


@_attrs_define
class SwitchCommitRequestBody:
    """
    Attributes:
        commit_hash (str): Hash of the commit to switch to
        project_id (str): ID of the project
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    commit_hash: str
    project_id: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        commit_hash = self.commit_hash

        project_id = self.project_id

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "commit_hash": commit_hash,
                "project_id": project_id,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        commit_hash = d.pop("commit_hash")

        project_id = d.pop("project_id")

        schema = d.pop("$schema", UNSET)

        switch_commit_request_body = cls(
            commit_hash=commit_hash,
            project_id=project_id,
            schema=schema,
        )

        return switch_commit_request_body
