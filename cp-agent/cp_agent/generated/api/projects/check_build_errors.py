from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.build_error_response_body import BuildErrorResponseBody
from ...models.error_model import ErrorModel
from ...models.project_operation_request_body import ProjectOperationRequestBody
from ...types import Response


def _get_kwargs(
    *,
    body: ProjectOperationRequestBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/projects/check-errors",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[BuildErrorResponseBody, ErrorModel]]:
    if response.status_code == 200:
        response_200 = BuildErrorResponseBody.from_dict(response.json())

        return response_200
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
) -> Response[Union[BuildErrorResponseBody, ErrorModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ProjectOperationRequestBody,
) -> Response[Union[BuildErrorResponseBody, ErrorModel]]:
    """Check build errors

     Check for build errors in a project

    Args:
        body (ProjectOperationRequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BuildErrorResponseBody, ErrorModel]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ProjectOperationRequestBody,
) -> Optional[Union[BuildErrorResponseBody, ErrorModel]]:
    """Check build errors

     Check for build errors in a project

    Args:
        body (ProjectOperationRequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BuildErrorResponseBody, ErrorModel]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ProjectOperationRequestBody,
) -> Response[Union[BuildErrorResponseBody, ErrorModel]]:
    """Check build errors

     Check for build errors in a project

    Args:
        body (ProjectOperationRequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BuildErrorResponseBody, ErrorModel]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ProjectOperationRequestBody,
) -> Optional[Union[BuildErrorResponseBody, ErrorModel]]:
    """Check build errors

     Check for build errors in a project

    Args:
        body (ProjectOperationRequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BuildErrorResponseBody, ErrorModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
