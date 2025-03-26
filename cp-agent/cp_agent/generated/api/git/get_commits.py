from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.get_commits_response_body import GetCommitsResponseBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: str,
    cursor: Union[Unset, str] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["project_id"] = project_id

    params["cursor"] = cursor

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/git/commits",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorModel, GetCommitsResponseBody]]:
    if response.status_code == 200:
        response_200 = GetCommitsResponseBody.from_dict(response.json())

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
) -> Response[Union[ErrorModel, GetCommitsResponseBody]]:
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
    cursor: Union[Unset, str] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Response[Union[ErrorModel, GetCommitsResponseBody]]:
    """Get commit history

     Get list of commits in the repository

    Args:
        project_id (str): ID of the project
        cursor (Union[Unset, str]): Cursor for pagination (commit hash)
        limit (Union[Unset, int]): Maximum number of commits to return (default: 20)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, GetCommitsResponseBody]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        cursor=cursor,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    cursor: Union[Unset, str] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Optional[Union[ErrorModel, GetCommitsResponseBody]]:
    """Get commit history

     Get list of commits in the repository

    Args:
        project_id (str): ID of the project
        cursor (Union[Unset, str]): Cursor for pagination (commit hash)
        limit (Union[Unset, int]): Maximum number of commits to return (default: 20)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, GetCommitsResponseBody]
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        cursor=cursor,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    cursor: Union[Unset, str] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Response[Union[ErrorModel, GetCommitsResponseBody]]:
    """Get commit history

     Get list of commits in the repository

    Args:
        project_id (str): ID of the project
        cursor (Union[Unset, str]): Cursor for pagination (commit hash)
        limit (Union[Unset, int]): Maximum number of commits to return (default: 20)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, GetCommitsResponseBody]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        cursor=cursor,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    cursor: Union[Unset, str] = UNSET,
    limit: Union[Unset, int] = UNSET,
) -> Optional[Union[ErrorModel, GetCommitsResponseBody]]:
    """Get commit history

     Get list of commits in the repository

    Args:
        project_id (str): ID of the project
        cursor (Union[Unset, str]): Cursor for pagination (commit hash)
        limit (Union[Unset, int]): Maximum number of commits to return (default: 20)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, GetCommitsResponseBody]
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            cursor=cursor,
            limit=limit,
        )
    ).parsed
