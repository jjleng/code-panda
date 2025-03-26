from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.get_file_content_response_body import GetFileContentResponseBody
from ...types import UNSET, Response


def _get_kwargs(
    *,
    project_id: str,
    file_path: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["project_id"] = project_id

    params["file_path"] = file_path

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/files/content",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorModel, GetFileContentResponseBody]]:
    if response.status_code == 200:
        response_200 = GetFileContentResponseBody.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = ErrorModel.from_dict(response.json())

        return response_400
    if response.status_code == 422:
        response_422 = ErrorModel.from_dict(response.json())

        return response_422
    if response.status_code == 500:
        response_500 = ErrorModel.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorModel, GetFileContentResponseBody]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    file_path: str,
) -> Response[Union[ErrorModel, GetFileContentResponseBody]]:
    """Get file content

     Get the content of a specific file

    Args:
        project_id (str): ID of the project
        file_path (str): Path to the file relative to project path

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, GetFileContentResponseBody]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        file_path=file_path,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    file_path: str,
) -> Optional[Union[ErrorModel, GetFileContentResponseBody]]:
    """Get file content

     Get the content of a specific file

    Args:
        project_id (str): ID of the project
        file_path (str): Path to the file relative to project path

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, GetFileContentResponseBody]
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        file_path=file_path,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    file_path: str,
) -> Response[Union[ErrorModel, GetFileContentResponseBody]]:
    """Get file content

     Get the content of a specific file

    Args:
        project_id (str): ID of the project
        file_path (str): Path to the file relative to project path

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, GetFileContentResponseBody]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        file_path=file_path,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    file_path: str,
) -> Optional[Union[ErrorModel, GetFileContentResponseBody]]:
    """Get file content

     Get the content of a specific file

    Args:
        project_id (str): ID of the project
        file_path (str): Path to the file relative to project path

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, GetFileContentResponseBody]
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            file_path=file_path,
        )
    ).parsed
