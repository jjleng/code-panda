from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetFileContentResponseBody")


@_attrs_define
class GetFileContentResponseBody:
    """
    Attributes:
        content (str): Content of the file (base64 encoded for binary files)
        mime_type (str): MIME type of the file
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    content: str
    mime_type: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        mime_type = self.mime_type

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "content": content,
                "mime_type": mime_type,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        content = d.pop("content")

        mime_type = d.pop("mime_type")

        schema = d.pop("$schema", UNSET)

        get_file_content_response_body = cls(
            content=content,
            mime_type=mime_type,
            schema=schema,
        )

        return get_file_content_response_body
