from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.get_commit_diff_response_body import GetCommitDiffResponseBody
from ...types import UNSET, Response


def _get_kwargs(
    *,
    project_id: str,
    commit_hash: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["project_id"] = project_id

    params["commit_hash"] = commit_hash

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/git/commits/diff",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorModel, GetCommitDiffResponseBody]]:
    if response.status_code == 200:
        response_200 = GetCommitDiffResponseBody.from_dict(response.json())

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
) -> Response[Union[ErrorModel, GetCommitDiffResponseBody]]:
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
    commit_hash: str,
) -> Response[Union[ErrorModel, GetCommitDiffResponseBody]]:
    """Get commit diff

     Get diff for a specific commit

    Args:
        project_id (str): ID of the project
        commit_hash (str): Hash of the commit

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, GetCommitDiffResponseBody]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        commit_hash=commit_hash,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    commit_hash: str,
) -> Optional[Union[ErrorModel, GetCommitDiffResponseBody]]:
    """Get commit diff

     Get diff for a specific commit

    Args:
        project_id (str): ID of the project
        commit_hash (str): Hash of the commit

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, GetCommitDiffResponseBody]
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        commit_hash=commit_hash,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    commit_hash: str,
) -> Response[Union[ErrorModel, GetCommitDiffResponseBody]]:
    """Get commit diff

     Get diff for a specific commit

    Args:
        project_id (str): ID of the project
        commit_hash (str): Hash of the commit

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, GetCommitDiffResponseBody]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        commit_hash=commit_hash,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    project_id: str,
    commit_hash: str,
) -> Optional[Union[ErrorModel, GetCommitDiffResponseBody]]:
    """Get commit diff

     Get diff for a specific commit

    Args:
        project_id (str): ID of the project
        commit_hash (str): Hash of the commit

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, GetCommitDiffResponseBody]
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            commit_hash=commit_hash,
        )
    ).parsed
