// This file is auto-generated by @hey-api/openapi-ts

import { createClient, createConfig, type Options, formDataBodySerializer } from '@hey-api/client-fetch';
import type { ChatApiV1ChatPostData, ChatApiV1ChatPostError, HeartbeatApiV1HeartbeatPostData, HeartbeatApiV1HeartbeatPostResponse, HeartbeatApiV1HeartbeatPostError, CreateProjectApiV1ProjectsPostData, CreateProjectApiV1ProjectsPostResponse, CreateProjectApiV1ProjectsPostError, IntegrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePostData, IntegrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePostResponse, IntegrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePostError, SetProjectSecretApiV1ProjectsProjectIdSecretsPostData, SetProjectSecretApiV1ProjectsProjectIdSecretsPostResponse, SetProjectSecretApiV1ProjectsProjectIdSecretsPostError, UploadAssetsApiV1ProjectsProjectIdUploadPostData, UploadAssetsApiV1ProjectsProjectIdUploadPostResponse, UploadAssetsApiV1ProjectsProjectIdUploadPostError, GenerateSummaryApiV1ProjectsProjectIdGenerateSummaryPostData, GenerateSummaryApiV1ProjectsProjectIdGenerateSummaryPostResponse, GenerateSummaryApiV1ProjectsProjectIdGenerateSummaryPostError, ExecuteMigrationApiV1ProjectsProjectIdMigrationsPostData, ExecuteMigrationApiV1ProjectsProjectIdMigrationsPostResponse, ExecuteMigrationApiV1ProjectsProjectIdMigrationsPostError, ListProjectPathsApiV1ProjectsProjectIdPathsGetData, ListProjectPathsApiV1ProjectsProjectIdPathsGetResponse, ListProjectPathsApiV1ProjectsProjectIdPathsGetError, DownloadProjectApiV1ProjectsProjectIdDownloadGetData, DownloadProjectApiV1ProjectsProjectIdDownloadGetError, SwitchCommitApiV1ProjectsProjectIdSwitchCommitPostData, SwitchCommitApiV1ProjectsProjectIdSwitchCommitPostResponse, SwitchCommitApiV1ProjectsProjectIdSwitchCommitPostError, CreateSubdomainApiV1ProjectsProjectIdSubdomainPutData, CreateSubdomainApiV1ProjectsProjectIdSubdomainPutResponse, CreateSubdomainApiV1ProjectsProjectIdSubdomainPutError, EditProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPutData, EditProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPutResponse, EditProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPutError, DeleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDeleteData, DeleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDeleteResponse, DeleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDeleteError, GetProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGetData, GetProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGetResponse, GetProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGetError, PublishProjectApiV1ProjectsProjectIdPublishPostData, PublishProjectApiV1ProjectsProjectIdPublishPostResponse, PublishProjectApiV1ProjectsProjectIdPublishPostError, GetDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGetData, GetDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGetResponse, GetDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGetError, GetCreditsApiV1SubscriptionsCreditsGetData, GetCreditsApiV1SubscriptionsCreditsGetResponse, RootGetData, RootGetResponse, HealthCheckHealthGetData, HealthCheckHealthGetResponse, MetricsMetricsGetData } from './types.gen';

export const client = createClient(createConfig());

/**
 * Chat
 * Process a chat message with streaming response.
 *
 * Args:
 * request: The chat request containing MessageContent and project info
 * user: Optional authenticated user, required in hosted mode
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * A streaming response of SSE events
 */
export const chatApiV1ChatPost = <ThrowOnError extends boolean = false>(options: Options<ChatApiV1ChatPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<unknown, ChatApiV1ChatPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/chat/',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Heartbeat
 * Record heartbeat for project.
 */
export const heartbeatApiV1HeartbeatPost = <ThrowOnError extends boolean = false>(options?: Options<HeartbeatApiV1HeartbeatPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<HeartbeatApiV1HeartbeatPostResponse, HeartbeatApiV1HeartbeatPostError, ThrowOnError>({
        url: '/api/v1/heartbeat/',
        ...options
    });
};

/**
 * Create Project
 * Create a new project.
 *
 * Args:
 * request: Project creation request containing project_id and optional name
 * user: Optional authenticated user, required in hosted mode
 *
 * Returns:
 * Project: The created project details
 *
 * Raises:
 * HTTPException: 400 if project ID is invalid
 * HTTPException: 403 if user authentication is required but missing
 * HTTPException: 500 if project creation fails
 */
export const createProjectApiV1ProjectsPost = <ThrowOnError extends boolean = false>(options: Options<CreateProjectApiV1ProjectsPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<CreateProjectApiV1ProjectsPostResponse, CreateProjectApiV1ProjectsPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Integrate Supabase With Project
 * Integrate Supabase with an existing project.
 *
 * Args:
 * project_id: The ID of the project to integrate Supabase with
 * background_tasks: FastAPI background tasks
 * user: Optional authenticated user, required in hosted mode
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * Dict with success message
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist
 * HTTPException: 403 if user authentication is required but missing
 * HTTPException: 500 if integration fails
 */
export const integrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePost = <ThrowOnError extends boolean = false>(options: Options<IntegrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePostData, ThrowOnError>) => {
    return (options?.client ?? client).post<IntegrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePostResponse, IntegrateSupabaseWithProjectApiV1ProjectsProjectIdIntegrateSupabasePostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/integrate-supabase',
        ...options
    });
};

/**
 * Set Project Secret
 * Add or update a secret in the project's Supabase instance.
 *
 * Args:
 * project_id: The ID of the project
 * request: Secret request containing name and value
 * user: Optional authenticated user, required in hosted mode
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * Dict with success message
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist
 * HTTPException: 403 if user authentication is required but missing
 * HTTPException: 500 if setting the secret fails
 */
export const setProjectSecretApiV1ProjectsProjectIdSecretsPost = <ThrowOnError extends boolean = false>(options: Options<SetProjectSecretApiV1ProjectsProjectIdSecretsPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<SetProjectSecretApiV1ProjectsProjectIdSecretsPostResponse, SetProjectSecretApiV1ProjectsProjectIdSecretsPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/secrets',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Upload Assets
 * Upload multiple assets to a project's public directory.
 *
 * Args:
 * project_id: The ID of the project
 * files: List of files to upload
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * Dict containing success message and uploaded file information
 *
 * Raises:
 * HTTPException: If the project doesn't exist or upload fails
 */
export const uploadAssetsApiV1ProjectsProjectIdUploadPost = <ThrowOnError extends boolean = false>(options: Options<UploadAssetsApiV1ProjectsProjectIdUploadPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<UploadAssetsApiV1ProjectsProjectIdUploadPostResponse, UploadAssetsApiV1ProjectsProjectIdUploadPostError, ThrowOnError>({
        ...formDataBodySerializer,
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/upload',
        ...options,
        headers: {
            'Content-Type': null,
            ...options?.headers
        }
    });
};

/**
 * Generate Summary
 * Generate a project name and description based on the user's first message.
 *
 * Args:
 * project_id: The ID of the project
 * request: Contains the user's message
 * user: Optional authenticated user, required in hosted mode
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * Generated name and description for the project
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist
 * HTTPException: 500 if operation fails
 */
export const generateSummaryApiV1ProjectsProjectIdGenerateSummaryPost = <ThrowOnError extends boolean = false>(options: Options<GenerateSummaryApiV1ProjectsProjectIdGenerateSummaryPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<GenerateSummaryApiV1ProjectsProjectIdGenerateSummaryPostResponse, GenerateSummaryApiV1ProjectsProjectIdGenerateSummaryPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/generate-summary',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Execute Migration
 * Execute a SQL migration against the project's Supabase database.
 *
 * Args:
 * project_id: The ID of the project
 * migration: Migration request containing SQL to execute and optional name
 * user: Optional authenticated user, required in hosted mode
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * MigrationResponse: Migration execution details including success status and results
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist
 * HTTPException: 400 if SQL is empty or Supabase is not integrated
 * HTTPException: 403 if user authentication is required but missing
 * HTTPException: 500 if migration execution fails
 */
export const executeMigrationApiV1ProjectsProjectIdMigrationsPost = <ThrowOnError extends boolean = false>(options: Options<ExecuteMigrationApiV1ProjectsProjectIdMigrationsPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<ExecuteMigrationApiV1ProjectsProjectIdMigrationsPostResponse, ExecuteMigrationApiV1ProjectsProjectIdMigrationsPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/migrations',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * List Project Paths
 * List all pages/routes in a Vite project.
 *
 * Args:
 * project_id: The ID of the project
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * ListProjectPathsResponse: List of page paths found in the project
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist or directory not found
 * HTTPException: 500 if operation fails
 */
export const listProjectPathsApiV1ProjectsProjectIdPathsGet = <ThrowOnError extends boolean = false>(options: Options<ListProjectPathsApiV1ProjectsProjectIdPathsGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<ListProjectPathsApiV1ProjectsProjectIdPathsGetResponse, ListProjectPathsApiV1ProjectsProjectIdPathsGetError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/paths',
        ...options
    });
};

/**
 * Download Project
 * Download the source code of a project as a zip file.
 *
 * Args:
 * project_id: The ID of the project
 * background_tasks: FastAPI background tasks for cleanup
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * FileResponse: A zip file containing the project source code, respecting .gitignore
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist or directory not found
 * HTTPException: 500 if operation fails
 */
export const downloadProjectApiV1ProjectsProjectIdDownloadGet = <ThrowOnError extends boolean = false>(options: Options<DownloadProjectApiV1ProjectsProjectIdDownloadGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<unknown, DownloadProjectApiV1ProjectsProjectIdDownloadGetError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/download',
        ...options
    });
};

/**
 * Switch Commit
 * Switch the project's working directory to a specific git commit.
 *
 * Args:
 * project_id: The ID of the project.
 * request: Request containing the commit hash.
 * _: Dependency that verifies the user owns the project.
 *
 * Returns:
 * SwitchCommitResponse: Indicates success or failure.
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist.
 * HTTPException: 500 if switching commit fails.
 */
export const switchCommitApiV1ProjectsProjectIdSwitchCommitPost = <ThrowOnError extends boolean = false>(options: Options<SwitchCommitApiV1ProjectsProjectIdSwitchCommitPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<SwitchCommitApiV1ProjectsProjectIdSwitchCommitPostResponse, SwitchCommitApiV1ProjectsProjectIdSwitchCommitPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/switch-commit',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Create Subdomain
 * Create a project's custom subdomain.
 *
 * Creates a production domain for the project if none exists yet.
 * If a production subdomain already exists, returns an error.
 *
 * Args:
 * project_id: The ID of the project
 * request: The subdomain update request
 * user: The authenticated user
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * SubdomainUpdateResponse: Response containing the subdomain info
 *
 * Raises:
 * HTTPException: If subdomain is invalid or production subdomain already exists
 */
export const createSubdomainApiV1ProjectsProjectIdSubdomainPut = <ThrowOnError extends boolean = false>(options: Options<CreateSubdomainApiV1ProjectsProjectIdSubdomainPutData, ThrowOnError>) => {
    return (options?.client ?? client).put<CreateSubdomainApiV1ProjectsProjectIdSubdomainPutResponse, CreateSubdomainApiV1ProjectsProjectIdSubdomainPutError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/subdomain',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Edit Project Subdomain
 * Edit a project's existing production subdomain.
 *
 * This will rename the subdomain in the database and update the Cloudflare KV mapping.
 * Original content in R2 will remain unchanged.
 *
 * Args:
 * project_id: The ID of the project
 * request: The subdomain edit request containing the current and new subdomain
 * user: The authenticated user
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * SubdomainUpdateResponse: Response containing the updated subdomain info
 *
 * Raises:
 * HTTPException: If subdomain is invalid, doesn't exist, or the new name is already taken
 */
export const editProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPut = <ThrowOnError extends boolean = false>(options: Options<EditProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPutData, ThrowOnError>) => {
    return (options?.client ?? client).put<EditProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPutResponse, EditProjectSubdomainApiV1ProjectsProjectIdSubdomainEditPutError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/subdomain/edit',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Delete Subdomain
 * Delete a project's production subdomain and its associated resources.
 *
 * This will:
 * 1. Delete the subdomain record from the database
 * 2. Delete the Cloudflare KV mapping
 * 3. Create an audit record for later R2 content cleanup
 *
 * Args:
 * project_id: The ID of the project
 * domain: The full domain name to delete (e.g., my-project.yourdomain.com)
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * SubdomainDeleteResponse: Response confirming deletion
 *
 * Raises:
 * HTTPException: If the domain doesn't exist or deletion fails
 */
export const deleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDelete = <ThrowOnError extends boolean = false>(options: Options<DeleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDeleteData, ThrowOnError>) => {
    return (options?.client ?? client).delete<DeleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDeleteResponse, DeleteSubdomainApiV1ProjectsProjectIdSubdomainDomainDeleteError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/subdomain/{domain}',
        ...options
    });
};

/**
 * Get Project Publish History
 * Get the publish history for a project.
 *
 * This returns the site_domains records which contain the publishing info.
 *
 * Args:
 * project_id: The ID of the project
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * List of site domains with publish history information
 */
export const getProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGet = <ThrowOnError extends boolean = false>(options: Options<GetProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<GetProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGetResponse, GetProjectPublishHistoryApiV1ProjectsProjectIdPublishHistoryGetError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/publish-history',
        ...options
    });
};

/**
 * Publish Project
 * Publish a project to selected domains.
 *
 * This endpoint builds the project and deploys it to the selected domains.
 * Each domain gets created/updated and published in a single operation.
 *
 * Args:
 * project_id: The ID of the project
 * request: The publish request containing domain names to publish to
 * user: Authenticated user making the request
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * PublishResponse: Details of the publishing operation
 *
 * Raises:
 * HTTPException: 404 if project doesn't exist
 * HTTPException: 400 if no domains specified
 * HTTPException: 500 if publishing fails or SSL configuration fails
 */
export const publishProjectApiV1ProjectsProjectIdPublishPost = <ThrowOnError extends boolean = false>(options: Options<PublishProjectApiV1ProjectsProjectIdPublishPostData, ThrowOnError>) => {
    return (options?.client ?? client).post<PublishProjectApiV1ProjectsProjectIdPublishPostResponse, PublishProjectApiV1ProjectsProjectIdPublishPostError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/publish',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });
};

/**
 * Get Domain Status
 * Get the status of a custom domain's SSL configuration.
 *
 * This endpoint only works for custom domains, not subdomains.
 * It will check the SSL status and verification status in Cloudflare.
 *
 * Args:
 * project_id: The ID of the project
 * domain: The domain name to check
 * _: Dependency that verifies the user owns the project
 *
 * Returns:
 * Dict with domain status information
 *
 * Raises:
 * HTTPException: 400 if domain is not a custom domain
 * HTTPException: 404 if domain not found
 * HTTPException: 500 if status check fails
 */
export const getDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGet = <ThrowOnError extends boolean = false>(options: Options<GetDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<GetDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGetResponse, GetDomainStatusApiV1ProjectsProjectIdDomainStatusDomainGetError, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/projects/{project_id}/domain-status/{domain}',
        ...options
    });
};

/**
 * Get Credits
 */
export const getCreditsApiV1SubscriptionsCreditsGet = <ThrowOnError extends boolean = false>(options?: Options<GetCreditsApiV1SubscriptionsCreditsGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<GetCreditsApiV1SubscriptionsCreditsGetResponse, unknown, ThrowOnError>({
        security: [
            {
                scheme: 'bearer',
                type: 'http'
            }
        ],
        url: '/api/v1/subscriptions/credits',
        ...options
    });
};

/**
 * Root
 * Root endpoint.
 */
export const rootGet = <ThrowOnError extends boolean = false>(options?: Options<RootGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<RootGetResponse, unknown, ThrowOnError>({
        url: '/',
        ...options
    });
};

/**
 * Health Check
 * Health check endpoint.
 */
export const healthCheckHealthGet = <ThrowOnError extends boolean = false>(options?: Options<HealthCheckHealthGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<HealthCheckHealthGetResponse, unknown, ThrowOnError>({
        url: '/health',
        ...options
    });
};

/**
 * Metrics
 * Prometheus metrics endpoint.
 */
export const metricsMetricsGet = <ThrowOnError extends boolean = false>(options?: Options<MetricsMetricsGetData, ThrowOnError>) => {
    return (options?.client ?? client).get<unknown, unknown, ThrowOnError>({
        url: '/metrics',
        ...options
    });
};