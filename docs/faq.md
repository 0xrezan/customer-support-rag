# Frequently Asked Questions

## Account & Billing

### How do I reset my password?
Go to the login page and click **Forgot Password**. Enter your email and we'll send a reset link. The link expires in 1 hour. If you don't see the email, check your spam folder. If you still can't find it, contact support@archtech.dev.

### Can I change my email address?
Yes. Go to **Settings → Profile → Email** and enter your new address. You'll need to verify the new email before the change takes effect. Your old email will stop working immediately after verification.

### How do I cancel my subscription?
Go to **Settings → Billing → Cancel Plan**. Your workspace will remain active until the end of the current billing period. After that, it downgrades to the Free plan. Your data is kept for 90 days — you can reactivate anytime within that window without losing anything.

### Do you offer refunds?
We offer a full refund within the first 14 days of any paid plan. After that, we don't offer partial refunds, but you can cancel anytime to avoid future charges. Contact support@archtech.dev for refund requests.

### Can I switch between monthly and annual billing?
Yes. Go to **Settings → Billing → Change Plan**. Annual billing gives you 2 months free (pay for 10, get 12). When switching from monthly to annual, you'll receive a prorated credit for the remaining days of the current month.

### What happens if my payment fails?
We retry the payment 3 times over 7 days. You'll receive an email notification after each failed attempt. If all retries fail, your workspace is downgraded to the Free plan. No data is deleted — upgrade again to restore full access.

## Projects & Tasks

### How many projects can I create?
Free plan: 3 projects. Pro and Business plans: unlimited.

### Can I move tasks between projects?
Yes. Open the task, click the **⋮** menu in the top right, and select **Move to Project**. The task keeps its comments, attachments, and history. Assignee is preserved if the person is a member of the destination project; otherwise it's unassigned.

### Can I create recurring tasks?
Yes. When editing a task, click **Set Recurrence** and choose a pattern: daily, weekly, biweekly, monthly, or custom. When a recurring task is marked as done, a new copy is automatically created with the next due date.

### How do subtasks work?
Each task can have a checklist of subtasks. Subtasks are simple text items with a checkbox. They don't have their own assignees, due dates, or comments. If you need full-featured sub-items, create separate tasks and link them using the **Related Tasks** field.

### What's the difference between Labels and Priority?
**Priority** is a single value (Low, Medium, High, Urgent) used for sorting and filtering. **Labels** are custom, color-coded tags you can create for anything — departments, features, clients, sprints. A task can have multiple labels but only one priority.

### Can I set up automations?
Yes (Pro and Business plans). Go to **Project Settings → Automations**. Examples:
- When a task moves to "Done" → notify the project owner
- When a task is overdue → change priority to Urgent
- When a task is assigned → send Slack message to the assignee

Business plan supports custom webhook automations and API triggers.

### How does the Gantt chart work?
Go to any project and switch to **Gantt view** (top right, next to Board and List views). Tasks are shown as horizontal bars on a timeline. Drag the edges to change start/end dates. Draw arrows between tasks to create dependencies. If task A depends on task B, moving B automatically shifts A.

Gantt view is available on Pro and Business plans.

## Integrations

### How do I connect Slack?
Go to **Settings → Integrations → Slack → Connect**. Authorize Arch Tech in your Slack workspace. Then choose which project events should post to which Slack channels. You can configure per-project or per-workspace.

### How does the GitHub integration work?
Connect your GitHub account in **Settings → Integrations → GitHub**. Then, in any task, paste a GitHub issue or PR URL. Arch Tech will display the status (open/merged/closed) directly on the task card. When a linked PR is merged, the task can be automatically moved to "Done".

### Can I import from Trello, Asana, or Jira?
Yes. Go to **Settings → Import Data** and select your source. We support:
- **Trello**: boards → projects, cards → tasks, checklists → subtasks
- **Asana**: projects → projects, tasks → tasks, subtasks → subtasks
- **Jira**: projects → projects, issues → tasks (story points mapped to time estimates)

Attachments and comments are imported. User assignments are matched by email address.

### Is there an API?
Yes. Full REST API documented at https://api.archtech.dev/docs. API keys are managed in **Settings → API Keys**. Rate limit: 100 requests per minute per key. The API supports everything the web app does: create/read/update/delete projects, tasks, comments, and members.

## Collaboration

### How do guest accounts work?
Guests are external collaborators (clients, contractors) who can access specific projects but not the entire workspace. Guests can view tasks, leave comments, and upload files. They cannot create projects, invite other people, or see billing information. Available on Pro (5 guests) and Business (unlimited).

### Can I @mention people in comments?
Yes. Type `@` followed by a name. The person will receive a notification. You can mention any workspace member or guest who has access to the project.

### Is there real-time collaboration?
Yes. Multiple people can view and edit the same project board simultaneously. Changes appear instantly for everyone. Task descriptions support collaborative editing — you'll see other people's cursors in real time (similar to Google Docs).

### Can I export my data?
Yes. Go to **Settings → Data Export**. You can export:
- All projects and tasks as CSV or JSON
- All attachments as a ZIP file
- Audit log as CSV

Export is available to Admins only. Processing takes up to 1 hour for large workspaces. You'll receive a download link via email.

## Technical

### What browsers are supported?
Chrome 90+, Firefox 90+, Safari 15+, Edge 90+. We don't support Internet Explorer.

### Is there an offline mode?
The mobile app supports offline mode — you can view tasks and make changes that sync when you reconnect. The web app requires an internet connection.

### What is your uptime guarantee?
Free and Pro plans: best-effort availability (historically 99.8%). Business plan: 99.9% uptime SLA with service credits if we fall below.

### Where is my data stored?
Your data is stored in AWS data centers. When you create a workspace, you choose a region:
- **EU** (Frankfurt, Germany) — for European businesses, GDPR-optimized
- **US** (Virginia, USA) — for North American businesses

Data does not move between regions after workspace creation.

### How long do you retain deleted data?
When you delete a task, it goes to the project Trash and stays there for 30 days. After that, it's permanently deleted. When you delete a project, it's recoverable for 30 days. When you cancel your account, all data is kept for 90 days, then permanently purged.
