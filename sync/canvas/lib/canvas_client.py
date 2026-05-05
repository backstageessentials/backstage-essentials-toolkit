"""Canvas LMS REST API client.

Wraps the Canvas REST API at https://<host>/api/v1/ with bearer token auth,
rate limit handling, and clean Python methods for the endpoints we use.

Auth pattern: manual access token. The user generates a token in Canvas at
Account, Settings, New Access Token, copies it into .env as CANVAS_API_TOKEN.
The base URL goes in .env as CANVAS_API_URL (institution Canvas instance).

Dry-run mode: when constructed with dry_run=True, the client never hits the
network. Every method records the would-be request payload onto self.recorded
and returns a deterministic stub response shaped like the real API. The sync
flow can then run end to end against a real course repo without any account.
"""

import logging
import time
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# Canvas allows roughly 200 requests/min/user. Stay well under.
DEFAULT_RETRY_COUNT = 3
DEFAULT_BACKOFF_BASE = 2.0  # seconds


class CanvasError(Exception):
    """Raised when the Canvas API returns an error we cannot recover from."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CanvasClient:
    """Minimal Canvas LMS API client for course content sync."""

    def __init__(self, api_url: str, api_token: str, account_id: Optional[str] = None,
                 dry_run: bool = False):
        if not dry_run:
            if not api_token or api_token.startswith("your_"):
                raise CanvasError("CANVAS_API_TOKEN is missing or still a placeholder.")
            if not api_url or api_url.startswith("https://your-"):
                raise CanvasError("CANVAS_API_URL is missing or still a placeholder.")

        # Normalize: accept either bare host or full base URL with /api/v1.
        self.api_url = (api_url or "").rstrip("/")
        if not self.api_url.endswith("/api/v1"):
            self.api_url = f"{self.api_url}/api/v1"

        self.api_token = api_token or ""
        self.account_id = account_id
        self.dry_run = dry_run

        # Counter so dry-run stub IDs are unique within a session.
        self._dry_id_counter = 1000
        self.recorded: list[dict] = []  # list of {method, path, json|params}

        if not dry_run:
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            })
        else:
            self.session = None

    # -------- low-level request helpers --------

    def _next_dry_id(self) -> int:
        self._dry_id_counter += 1
        return self._dry_id_counter

    def _record(self, method: str, path: str, **kwargs) -> None:
        entry = {"method": method, "path": path}
        if "json" in kwargs:
            entry["json"] = kwargs["json"]
        if "params" in kwargs:
            entry["params"] = kwargs["params"]
        self.recorded.append(entry)

    def _dry_response(self, method: str, path: str, **kwargs) -> dict:
        """Return a synthetic response that resembles a real Canvas reply."""
        if method == "GET":
            # Default to empty list for collections, empty dict for items.
            return {"items": []} if path.endswith("s") else {}

        # POST / PUT / DELETE: invent a plausible object with an id.
        body = kwargs.get("json", {}) or {}
        stub: dict = {"id": self._next_dry_id()}
        # Echo back interesting fields when present.
        for key in ("name", "title", "position", "course_code",
                    "module_id", "page_id", "url", "quiz_type"):
            if key in body:
                stub[key] = body[key]
        # Some endpoints wrap the resource under a single key (e.g. {"course": {...}}).
        for wrapper in ("course", "module", "module_item", "wiki_page",
                        "quiz", "question", "page"):
            if wrapper in body and isinstance(body[wrapper], dict):
                for k, v in body[wrapper].items():
                    if k not in stub:
                        stub[k] = v
        return stub

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make a request with retry/backoff. Honors dry_run."""
        self._record(method, path, **kwargs)

        if self.dry_run:
            return self._dry_response(method, path, **kwargs)

        url = f"{self.api_url}{path}"

        for attempt in range(DEFAULT_RETRY_COUNT):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)

                if 200 <= response.status_code < 300:
                    if response.text:
                        return response.json()
                    return {}

                if response.status_code == 429:
                    retry_after = int(response.headers.get(
                        "Retry-After", DEFAULT_BACKOFF_BASE * (attempt + 1)
                    ))
                    logger.warning(f"Rate limited. Sleeping {retry_after}s before retry.")
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    backoff = DEFAULT_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}. Sleeping {backoff}s.")
                    time.sleep(backoff)
                    continue

                raise CanvasError(
                    f"API error {response.status_code} on {method} {path}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            except requests.RequestException as e:
                if attempt == DEFAULT_RETRY_COUNT - 1:
                    raise CanvasError(f"Network error on {method} {path}: {e}")
                backoff = DEFAULT_BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Network error. Sleeping {backoff}s.")
                time.sleep(backoff)

        raise CanvasError(f"Exhausted retries on {method} {path}")

    # -------- auth probe --------

    def test_auth(self) -> bool:
        """Verify the token works by hitting /users/self. True on success."""
        if self.dry_run:
            self._record("GET", "/users/self")
            return True
        try:
            self._request("GET", "/users/self")
            return True
        except CanvasError as e:
            if e.status_code in (401, 403):
                return False
            raise

    # -------- courses --------

    def list_account_courses(self, account_id: str) -> list[dict]:
        """List courses under a Canvas account."""
        result = self._request("GET", f"/accounts/{account_id}/courses",
                               params={"per_page": 100})
        # Real Canvas returns a JSON array; dry-run returns {"items": []}.
        if isinstance(result, list):
            return result
        return result.get("items", [])

    def find_course_by_code(self, account_id: str, course_code: str) -> Optional[dict]:
        """Find a course in the given account by course_code (we use the slug)."""
        for course in self.list_account_courses(account_id):
            if course.get("course_code") == course_code:
                return course
        return None

    def create_course(self, account_id: str, name: str, course_code: str) -> dict:
        """Create a new course. Returns the created course dict."""
        return self._request(
            "POST",
            f"/accounts/{account_id}/courses",
            json={"course": {"name": name, "course_code": course_code}},
        )

    def update_course_syllabus(self, course_id: int, syllabus_html: str) -> dict:
        """Set the course syllabus_body to the rendered course description."""
        return self._request(
            "PUT",
            f"/courses/{course_id}",
            json={"course": {"syllabus_body": syllabus_html}},
        )

    # -------- modules (units) --------

    def create_module(self, course_id: int, name: str, position: int) -> dict:
        return self._request(
            "POST",
            f"/courses/{course_id}/modules",
            json={"module": {"name": name, "position": position}},
        )

    def add_module_item(self, course_id: int, module_id: int, title: str,
                        item_type: str, content_id: Optional[int] = None,
                        page_url: Optional[str] = None,
                        position: Optional[int] = None) -> dict:
        """Attach a content item to a module.

        item_type is one of: Page, Quiz, Assignment, File, ExternalUrl, etc.
        For Page items, Canvas takes page_url (the page's slug) instead of content_id.
        """
        item: dict = {"title": title, "type": item_type}
        if position is not None:
            item["position"] = position
        if item_type == "Page" and page_url:
            item["page_url"] = page_url
        elif content_id is not None:
            item["content_id"] = content_id
        return self._request(
            "POST",
            f"/courses/{course_id}/modules/{module_id}/items",
            json={"module_item": item},
        )

    # -------- pages (lessons) --------

    def create_page(self, course_id: int, title: str, body_html: str,
                    published: bool = False) -> dict:
        return self._request(
            "POST",
            f"/courses/{course_id}/pages",
            json={"wiki_page": {
                "title": title,
                "body": body_html,
                "published": published,
            }},
        )

    def update_page(self, course_id: int, page_url: str, title: str,
                    body_html: str) -> dict:
        return self._request(
            "PUT",
            f"/courses/{course_id}/pages/{page_url}",
            json={"wiki_page": {"title": title, "body": body_html}},
        )

    # -------- quizzes (classic) --------

    def create_quiz(self, course_id: int, title: str, quiz_type: str = "assignment",
                    pass_threshold: float = 0.7, shuffle_answers: bool = True,
                    description_html: str = "") -> dict:
        return self._request(
            "POST",
            f"/courses/{course_id}/quizzes",
            json={"quiz": {
                "title": title,
                "quiz_type": quiz_type,
                "shuffle_answers": shuffle_answers,
                "scoring_policy": "keep_highest",
                "description": description_html,
                "show_correct_answers": True,
            }},
        )

    def add_quiz_question(self, course_id: int, quiz_id: int, question_name: str,
                          question_text: str, choices: list[dict],
                          points: int = 1) -> dict:
        """Add a multiple choice question to a classic quiz.

        choices: list of {"text": str, "correct": bool}. Canvas multiple-choice
        questions take answers with `answer_text` and `answer_weight` (100 for
        correct, 0 for incorrect).
        """
        answers = []
        for c in choices:
            answers.append({
                "answer_text": c["text"],
                "answer_weight": 100 if c.get("correct") else 0,
            })
        return self._request(
            "POST",
            f"/courses/{course_id}/quizzes/{quiz_id}/questions",
            json={"question": {
                "question_name": question_name,
                "question_text": question_text,
                "question_type": "multiple_choice_question",
                "points_possible": points,
                "answers": answers,
            }},
        )

    def update_quiz_question(self, course_id: int, quiz_id: int, question_id: int,
                              question_name: str, question_text: str,
                              choices: list[dict], points: int = 1) -> dict:
        answers = []
        for c in choices:
            answers.append({
                "answer_text": c["text"],
                "answer_weight": 100 if c.get("correct") else 0,
            })
        return self._request(
            "PUT",
            f"/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}",
            json={"question": {
                "question_name": question_name,
                "question_text": question_text,
                "question_type": "multiple_choice_question",
                "points_possible": points,
                "answers": answers,
            }},
        )

    def create_quiz_question_group(self, course_id: int, quiz_id: int, name: str,
                                    pick_count: int, question_points: float = 1) -> dict:
        """Create a question group inside a quiz.

        Used by the course final to pick N from a pool of M.
        """
        return self._request(
            "POST",
            f"/courses/{course_id}/quizzes/{quiz_id}/groups",
            json={"quiz_groups": [{
                "name": name,
                "pick_count": pick_count,
                "question_points": question_points,
            }]},
        )

    # -------- files (MicroSims, images) --------

    def upload_file_placeholder(self, course_id: int, filename: str,
                                  size: int, content_type: str) -> dict:
        """Step 1 of Canvas's two-step upload: request an upload URL.

        Phase 11 records the request but defers the second-step PUT to a
        future MicroSim/image embed pass. Lessons reference relative paths
        for now and the sync skill notes which files would need uploading.
        """
        return self._request(
            "POST",
            f"/courses/{course_id}/files",
            json={
                "name": filename,
                "size": size,
                "content_type": content_type,
                "parent_folder_path": "course files",
            },
        )

    # -------- URLs --------

    def admin_url_for_course(self, course_id: int) -> str:
        host = urlparse(self.api_url).netloc or "canvas.instructure.com"
        return f"https://{host}/courses/{course_id}"
