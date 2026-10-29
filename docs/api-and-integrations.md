# Arch Tech API & Integrations Guide

## REST API Overview

The Arch Tech API lets you programmatically manage projects, tasks, members, and comments. All endpoints are available at `https://api.archtech.dev/v1`.

### Authentication

Every request must include an API key in the `Authorization` header:

```
Authorization: Bearer at_live_abc123...
```

API keys are created in **Settings → API Keys**. Each key has a name, creation date, and last-used timestamp. You can create up to 10 keys per workspace. Keys can be revoked at any time.

**Important:** API keys grant full access to the workspace. Do not share them or commit them to version control. Use environment variables to store keys in your applications.

### Rate Limits

| Plan | Rate Limit |
|------|-----------|
| Free | 30 requests/minute |
| Pro | 100 requests/minute |
| Business | 500 requests/minute |

When you exceed the limit, the API returns HTTP 429 with a `Retry-After` header indicating how many seconds to wait. We recommend implementing exponential backoff in your integration.

### Response Format

All responses follow the same structure:

```json
{
  "ok": true,
  "data": { ... },
  "error": null
}
```

On error:

```json
{
  "ok": false,
  "data": null,
  "error": "Task not found"
}
```

HTTP status codes: 200 (success), 201 (created), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 429 (rate limited), 500 (server error).

### Common Endpoints

**Projects**
- `GET /v1/projects` — list all projects in the workspace
- `POST /v1/projects` — create a new project
- `GET /v1/projects/{id}` — get project details
- `PATCH /v1/projects/{id}` — update project name, description, or status
- `DELETE /v1/projects/{id}` — archive a project (recoverable for 30 days)

**Tasks**
- `GET /v1/projects/{id}/tasks` — list tasks in a project (supports `?status=`, `?assignee=`, `?label=`, `?sort=`)
- `POST /v1/projects/{id}/tasks` — create a task
- `GET /v1/tasks/{id}` — get task details including comments and attachments
- `PATCH /v1/tasks/{id}` — update any task field
- `DELETE /v1/tasks/{id}` — move task to trash

**Comments**
- `GET /v1/tasks/{id}/comments` — list comments on a task
- `POST /v1/tasks/{id}/comments` — add a comment (Markdown supported)

**Members**
- `GET /v1/members` — list workspace members and their roles
- `POST /v1/members/invite` — invite a new member by email
- `PATCH /v1/members/{id}` — change member role
- `DELETE /v1/members/{id}` — remove member from workspace

### Pagination

List endpoints return paginated results. Use `?page=1&per_page=50` parameters. The response includes:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 234,
    "total_pages": 5
  }
}
```

Default `per_page` is 50. Maximum is 200.

### Webhooks

Webhooks allow Arch Tech to notify your server when events happen. Configure them in **Settings → Integrations → Webhooks**.

**Supported events:**
- `task.created` — a new task was created
- `task.updated` — a task's status, assignee, priority, or due date changed
- `task.completed` — a task was marked as done
- `task.deleted` — a task was moved to trash
- `project.created` — a new project was created
- `member.joined` — someone accepted a workspace invitation
- `comment.created` — a new comment was posted

Each webhook delivery includes an `X-Webhook-Signature` header (HMAC-SHA256) so you can verify it came from Arch Tech. Your webhook secret is shown when you create the webhook endpoint.

Webhooks are retried 3 times with exponential backoff (10s, 60s, 300s) if your server returns a non-2xx status code. Failed deliveries are logged in **Settings → Integrations → Webhooks → Delivery Log**.

---

## Slack Integration

### Setup

1. Go to **Settings → Integrations → Slack**
2. Click **Connect to Slack** and authorize in your Slack workspace
3. Choose a default channel for notifications

### What Gets Posted

By default, these events trigger Slack messages:
- Task assigned to someone
- Task moved to "Done"
- Task overdue
- New comment with an @mention

You can customize which events post to which channels in **Project Settings → Slack**.

### Slash Commands

After connecting, you can use `/archtech` in Slack:
- `/archtech create [task title]` — create a task in the default project
- `/archtech search [keywords]` — search tasks across all projects
- `/archtech my tasks` — list your open tasks sorted by due date

---

## GitHub Integration

### Setup

1. Go to **Settings → Integrations → GitHub**
2. Click **Connect GitHub** and install the Arch Tech GitHub App on your repositories
3. Choose which repositories to link

### Features

**Link PRs to tasks:** Paste a GitHub PR URL in a task description or comment. Arch Tech shows the PR status (open, merged, closed) on the task card.

**Auto-close tasks:** When a linked PR is merged, the task automatically moves to "Done". Enable this per-project in **Project Settings → GitHub → Auto-complete tasks**.

**Branch creation:** From any task, click **Create Branch** to generate a branch name based on the task title (e.g., `feat/AT-142-add-user-export`). This copies the branch name to your clipboard.

**Commit references:** Include `AT-142` (task ID) in your commit message and it will appear in the task's activity log.

---

## Google Drive Integration

### Setup

1. Go to **Settings → Integrations → Google Drive**
2. Sign in with your Google account and grant file access

### Features

- Attach Google Docs, Sheets, and Slides directly to tasks (no download needed)
- Preview attached files inline without leaving Arch Tech
- When a Google Doc is updated, linked tasks show a "File updated" indicator
- Search task attachments by file name across all projects

---

## Zapier & Make (Integromat)

Arch Tech is available as a Zapier and Make app. This lets you connect Arch Tech to 5,000+ other tools without writing code.

**Popular automations:**
- New email in Gmail → create task in Arch Tech
- New row in Google Sheets → create task
- Task completed in Arch Tech → send email notification
- New form submission in Typeform → create task with form data
- Task created → add row to Airtable

Search for "Arch Tech" in the Zapier or Make app directory to get started.

---

## Troubleshooting Integrations

### Slack notifications stopped working
1. Check that the Slack bot is still installed: go to your Slack workspace settings → Apps → Arch Tech
2. Re-authorize: **Settings → Integrations → Slack → Reconnect**
3. Make sure the notification channel still exists (it may have been renamed or deleted)

### GitHub PR status not updating
1. Verify the GitHub App is installed on the correct repository
2. Check the webhook delivery log in GitHub: repo → Settings → Webhooks → Recent Deliveries
3. Re-install the integration: **Settings → Integrations → GitHub → Disconnect → Connect**

### API key returns 401
1. Make sure the key hasn't been revoked: **Settings → API Keys**
2. Check that the `Authorization` header format is `Bearer at_live_...` (not `Token` or `Basic`)
3. API keys are workspace-scoped — you can't use a key from workspace A to access workspace B
