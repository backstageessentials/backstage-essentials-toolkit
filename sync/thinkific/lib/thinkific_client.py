"""Thinkific REST API client.

Wraps the public API at https://api.thinkific.com/api/public/v1/ with
auth headers, rate limit handling, and clean Python methods for the
endpoints we actually use.
"""

import time
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.thinkific.com/api/public/v1"

# Rate limit: Thinkific allows ~120 requests per minute. We stay well under.
DEFAULT_RETRY_COUNT = 3
DEFAULT_BACKOFF_BASE = 2.0  # seconds


class ThinkificError(Exception):
    """Raised when the Thinkific API returns an error we can't recover from."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ThinkificClient:
    """Minimal Thinkific API client for course content sync."""

    def __init__(self, api_key: str, subdomain: str):
        if not api_key or api_key.startswith("your_"):
            raise ThinkificError("THINKIFIC_API_KEY is missing or still a placeholder.")
        if not subdomain or subdomain.startswith("your_"):
            raise ThinkificError("THINKIFIC_SUBDOMAIN is missing or still a placeholder.")

        self.api_key = api_key
        self.subdomain = subdomain
        self.session = requests.Session()
        self.session.headers.update({
            "X-Auth-API-Key": api_key,
            "X-Auth-Subdomain": subdomain,
            "Content-Type": "application/json",
        })

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make a request with retry and backoff on transient failures."""
        url = f"{API_BASE}{path}"

        for attempt in range(DEFAULT_RETRY_COUNT):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)

                # 2xx success
                if 200 <= response.status_code < 300:
                    if response.text:
                        return response.json()
                    return {}

                # 429 rate limited: back off and retry
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", DEFAULT_BACKOFF_BASE * (attempt + 1)))
                    logger.warning(f"Rate limited. Sleeping {retry_after}s before retry.")
                    time.sleep(retry_after)
                    continue

                # 5xx server error: back off and retry
                if response.status_code >= 500:
                    backoff = DEFAULT_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}. Sleeping {backoff}s.")
                    time.sleep(backoff)
                    continue

                # 4xx client error: do not retry, raise
                raise ThinkificError(
                    f"API error {response.status_code} on {method} {path}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            except requests.RequestException as e:
                if attempt == DEFAULT_RETRY_COUNT - 1:
                    raise ThinkificError(f"Network error on {method} {path}: {e}")
                backoff = DEFAULT_BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Network error. Sleeping {backoff}s.")
                time.sleep(backoff)

        raise ThinkificError(f"Exhausted retries on {method} {path}")

    def test_auth(self) -> bool:
        """Verify the API credentials work. Returns True on success."""
        try:
            self._request("GET", "/courses", params={"limit": 1})
            return True
        except ThinkificError as e:
            if e.status_code in (401, 403):
                return False
            raise

    def list_courses(self) -> list[dict]:
        """List all courses in the account."""
        result = self._request("GET", "/courses")
        return result.get("items", [])

    def find_course_by_slug(self, slug: str) -> Optional[dict]:
        """Find a course by its slug. Returns None if not found."""
        for course in self.list_courses():
            if course.get("slug") == slug:
                return course
        return None

    def create_course(self, name: str, slug: str, description: str = "") -> dict:
        """Create a new course. Returns the created course dict."""
        return self._request("POST", "/courses", json={
            "name": name,
            "slug": slug,
            "description": description,
        })

    def update_course(self, course_id: int, **fields) -> dict:
        """Update an existing course's fields."""
        return self._request("PUT", f"/courses/{course_id}", json=fields)

    def list_chapters(self, course_id: int) -> list[dict]:
        """List chapters in a course."""
        result = self._request("GET", "/chapters", params={"course_id": course_id})
        return result.get("items", [])

    def create_chapter(self, course_id: int, name: str, position: int) -> dict:
        """Create a chapter (unit) in a course."""
        return self._request("POST", "/chapters", json={
            "course_id": course_id,
            "name": name,
            "position": position,
        })

    def update_chapter(self, chapter_id: int, **fields) -> dict:
        """Update a chapter's fields."""
        return self._request("PUT", f"/chapters/{chapter_id}", json=fields)

    def create_lesson(self, chapter_id: int, name: str, body_html: str,
                      position: int) -> dict:
        """Create a lesson in a chapter. Body is HTML."""
        return self._request("POST", "/contents", json={
            "chapter_id": chapter_id,
            "content_type": "Lesson",
            "name": name,
            "lesson": {
                "body": body_html,
            },
            "position": position,
        })

    def update_lesson(self, content_id: int, name: str, body_html: str) -> dict:
        """Update a lesson's name and body."""
        return self._request("PUT", f"/contents/{content_id}", json={
            "name": name,
            "lesson": {"body": body_html},
        })

    def create_quiz(self, chapter_id: int, name: str, position: int,
                    pass_threshold: float = 0.7) -> dict:
        """Create a quiz in a chapter."""
        return self._request("POST", "/quizzes", json={
            "chapter_id": chapter_id,
            "name": name,
            "position": position,
            "pass_percentage": int(pass_threshold * 100),
        })

    def add_quiz_question(self, quiz_id: int, question_text: str,
                          choices: list[dict], explanation: str = "") -> dict:
        """Add a multiple choice question to a quiz.

        choices is a list of dicts with keys 'text' (str) and 'correct' (bool).
        """
        return self._request("POST", "/quiz_questions", json={
            "quiz_id": quiz_id,
            "type": "multiple_choice",
            "prompt": question_text,
            "explanation": explanation,
            "answers": [
                {"text": c["text"], "correct": c["correct"]}
                for c in choices
            ],
        })

    def update_quiz_question(self, question_id: int, question_text: str,
                              choices: list[dict], explanation: str = "") -> dict:
        """Update an existing quiz question."""
        return self._request("PUT", f"/quiz_questions/{question_id}", json={
            "prompt": question_text,
            "explanation": explanation,
            "answers": [
                {"text": c["text"], "correct": c["correct"]}
                for c in choices
            ],
        })

    def admin_url_for_course(self, course_id: int) -> str:
        """Return the admin URL for a course on the Thinkific site."""
        return f"https://{self.subdomain}.thinkific.com/admin/courses/{course_id}"
