from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddPackageRequestBody")


@_attrs_define
class AddPackageRequestBody:
    """
    Attributes:
        package_name (str): Name of the package to add
        project_id (str): ID of the project
        restart_server (bool): Whether to restart the server after installing the package (default: false)
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    package_name: str
    project_id: str
    restart_server: bool
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        package_name = self.package_name

        project_id = self.project_id

        restart_server = self.restart_server

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "package_name": package_name,
                "project_id": project_id,
                "restart_server": restart_server,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        package_name = d.pop("package_name")

        project_id = d.pop("project_id")

        restart_server = d.pop("restart_server")

        schema = d.pop("$schema", UNSET)

        add_package_request_body = cls(
            package_name=package_name,
            project_id=project_id,
            restart_server=restart_server,
            schema=schema,
        )

        return add_package_request_body
