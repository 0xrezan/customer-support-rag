"""Admin document list and status web UI — lightweight HTMX/Jinja pages."""

from __future__ import annotations

import html

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.api.deps import get_document_repo
from app.logging import get_logger
from app.security.admin_auth import require_admin_token

logger = get_logger(__name__)

router = APIRouter(
    prefix="/dashboard",
    dependencies=[Depends(require_admin_token)],
)


def _layout_head(*, admin_token: str = "") -> str:
    """Return the HTML head with HTMX and, if *admin_token* is provided, a
    global ``hx-headers`` attribute on ``<body>`` so every HTMX request
    includes the ``Authorization`` header (BUG-8 fix)."""
    hx_headers_attr = ""
    if admin_token:
        # Escape for safe HTML attribute embedding
        safe_token = html.escape(admin_token, quote=True)
        hx_headers_attr = f' hx-headers=\'{{"Authorization": "Bearer {safe_token}"}}\''
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Dashboard</title>
<script src="https://unpkg.com/htmx.org@1.9.12"></script>
<style>
body{{font-family:system-ui,sans-serif;margin:2rem;background:#f8f9fa}}
table{{border-collapse:collapse;width:100%}}
th,td{{text-align:left;padding:.5rem .75rem;border-bottom:1px solid #dee2e6}}
th{{background:#e9ecef}}
.badge{{display:inline-block;padding:.15rem .5rem;border-radius:.25rem;font-size:.8rem;color:#fff}}
.badge-indexed{{background:#198754}}
.badge-uploaded{{background:#0d6efd}}
.badge-parsing,.badge-indexing{{background:#ffc107;color:#000}}
.badge-failed_parse,.badge-failed_index{{background:#dc3545}}
.badge-deleted{{background:#6c757d}}
.badge-needs_ocr,.badge-needs_review{{background:#fd7e14}}
h1{{margin-bottom:1.5rem}}
.actions button{{margin-right:.25rem;cursor:pointer}}
.refresh{{margin-bottom:1rem}}
</style></head><body{hx_headers_attr}>"""


_LAYOUT_FOOT = "</body></html>"


def _status_badge(status: str) -> str:
    return f'<span class="badge badge-{status}">{status}</span>'


def _render_doc_table(docs: list) -> str:
    rows = ""
    for d in docs:
        st = d.status.value if hasattr(d.status, "value") else str(d.status)
        safe_name = html.escape(d.filename)
        rows += f"""<tr>
<td><code>{str(d.id)[:8]}...</code></td>
<td>{safe_name}</td>
<td>v{d.version}</td>
<td>{_status_badge(st)}</td>
<td>{d.chunk_count_actual or "-"}/{d.chunk_count_expected or "-"}</td>
<td>{d.file_size}</td>
<td>{d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else "-"}</td>
<td class="actions">
  <button hx-post="/api/v1/admin/documents/{d.id}/reindex"
          hx-swap="none" onclick="alert('Reindex enqueued')">Reindex</button>
  <button hx-delete="/api/v1/admin/documents/{d.id}"
          hx-swap="none" onclick="alert('Delete enqueued')">Delete</button>
</td></tr>"""
    return rows


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    document_repo=Depends(get_document_repo),
    admin_token: str = Depends(require_admin_token),
) -> str:
    """Render the admin document list page."""
    docs = await document_repo.list_all()
    rows = _render_doc_table(docs)

    return f"""{_layout_head(admin_token=admin_token)}
<h1>Document Management</h1>
<div class="refresh">
  <button hx-get="/api/v1/dashboard/documents-table" hx-target="#doc-table"
          hx-swap="innerHTML">Refresh</button>
  <span>Total: {len(docs)} documents</span>
</div>
<table>
<thead><tr>
  <th>ID</th><th>Filename</th><th>Version</th><th>Status</th>
  <th>Chunks</th><th>Size</th><th>Created</th><th>Actions</th>
</tr></thead>
<tbody id="doc-table">{rows}</tbody>
</table>
{_LAYOUT_FOOT}"""


@router.get("/documents-table", response_class=HTMLResponse)
async def documents_table_fragment(
    document_repo=Depends(get_document_repo),
) -> str:
    """HTMX fragment — just the table rows for refresh."""
    docs = await document_repo.list_all()
    return _render_doc_table(docs)


@router.get("/metrics", response_class=HTMLResponse)
async def metrics_page(
    request: Request,
    admin_token: str = Depends(require_admin_token),
) -> str:
    """Lightweight metrics dashboard over logs and feedback."""
    container = request.app.state.container

    # Gather basic stats
    try:
        from app.domain.services.report_service import ReportService

        report_svc = ReportService(container.db_session_factory)
        report = await report_svc.unanswered_report()
        feedback = await report_svc.feedback_summary()
    except Exception:
        report = None
        feedback = {}

    stats_html = "<p>Could not load metrics.</p>"
    if report:
        stats_html = f"""
<div style="display:flex;gap:2rem;flex-wrap:wrap">
  <div style="background:#fff;padding:1rem;border-radius:.5rem;min-width:200px">
    <h3>Questions</h3>
    <p>Total: <b>{report.total_questions}</b></p>
    <p>Answered: <b>{report.answered}</b></p>
    <p>Insufficient context: <b>{report.insufficient_context}</b></p>
    <p>Errors: <b>{report.errors}</b></p>
    <p>Unanswered rate: <b>{report.unanswered_rate:.1%}</b></p>
  </div>
  <div style="background:#fff;padding:1rem;border-radius:.5rem;min-width:200px">
    <h3>Feedback</h3>
    <p>Thumbs up: <b>{feedback.get("thumbs_up", 0)}</b></p>
    <p>Thumbs down: <b>{feedback.get("thumbs_down", 0)}</b></p>
  </div>
</div>"""

    unanswered_items = "".join(
        "<li>{q} ({s})</li>".format(
            q=html.escape(q["question"][:120]),
            s=html.escape(str(q["status"])),
        )
        for q in (report.top_unanswered[:20] if report else [])
    )

    return f"""{_layout_head(admin_token=admin_token)}
<h1>Metrics Dashboard</h1>
{stats_html}
<h2 style="margin-top:2rem">Top Unanswered Questions</h2>
<ul>
{unanswered_items}
</ul>
{_LAYOUT_FOOT}"""
