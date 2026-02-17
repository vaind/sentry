from __future__ import annotations

import logging

import orjson
from django.conf import settings
from urllib3 import HTTPConnectionPool

from sentry.net.http import connection_from_url
from sentry.seer.signed_seer_api import make_signed_seer_api_request

logger = logging.getLogger(__name__)

_code_review_connection_pool: HTTPConnectionPool | None = None


def _get_code_review_connection_pool() -> HTTPConnectionPool:
    global _code_review_connection_pool
    if _code_review_connection_pool is None:
        _code_review_connection_pool = connection_from_url(
            settings.SEER_AUTOFIX_URL,
            timeout=10,
        )
    return _code_review_connection_pool


def get_pr_comments(provider: str, owner: str, repo_name: str, pr_number: int) -> list[dict] | None:
    """Fetch all review comments from Seer for a given PR. Returns None on failure."""
    extra = {
        "provider": provider,
        "owner": owner,
        "repo_name": repo_name,
        "pr_number": pr_number,
    }
    try:
        response = make_signed_seer_api_request(
            connection_pool=_get_code_review_connection_pool(),
            path="/v1/automation/codegen/pr-review/comments",
            body=orjson.dumps(
                {
                    "provider": provider,
                    "owner": owner,
                    "repo": repo_name,
                    "pr_id": pr_number,
                }
            ),
            timeout=10,
        )
        if response.status == 200:
            return orjson.loads(response.data).get("comments", [])
        logger.warning(
            "seer.code_review.fetch_comments.bad_status",
            extra={"status": response.status, **extra},
        )
        return None
    except Exception:
        logger.exception(
            "seer.code_review.fetch_comments.failed",
            extra=extra,
        )
        return None
