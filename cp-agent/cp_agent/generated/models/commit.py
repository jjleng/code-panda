from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.commit_file import CommitFile


T = TypeVar("T", bound="Commit")


@_attrs_define
class Commit:
    """
    Attributes:
        date (str): Commit date
        files (Union[None, list['CommitFile']]): Changed files in the commit
        hash_ (str): Commit hash
        message (str): Commit message
    """

    date: str
    files: Union[None, list["CommitFile"]]
    hash_: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        date = self.date

        files: Union[None, list[dict[str, Any]]]
        if isinstance(self.files, list):
            files = []
            for files_type_0_item_data in self.files:
                files_type_0_item = files_type_0_item_data.to_dict()
                files.append(files_type_0_item)

        else:
            files = self.files

        hash_ = self.hash_

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "date": date,
                "files": files,
                "hash": hash_,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.commit_file import CommitFile

        d = src_dict.copy()
        date = d.pop("date")

        def _parse_files(data: object) -> Union[None, list["CommitFile"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                files_type_0 = []
                _files_type_0 = data
                for files_type_0_item_data in _files_type_0:
                    files_type_0_item = CommitFile.from_dict(files_type_0_item_data)

                    files_type_0.append(files_type_0_item)

                return files_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["CommitFile"]], data)

        files = _parse_files(d.pop("files"))

        hash_ = d.pop("hash")

        message = d.pop("message")

        commit = cls(
            date=date,
            files=files,
            hash_=hash_,
            message=message,
        )

        return commit
