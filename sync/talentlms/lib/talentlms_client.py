"""TalentLMS REST API client.

Wraps the per-account API at https://YOUR-DOMAIN.talentlms.com/api/v1/
with HTTP Basic Auth (api key as username, any string as password),
rate-limit handling, and clean Python methods for the endpoints the
sync flow actually uses.

Includes a dry-run mode (mirrors sync/canvas/lib/canvas_client.py) so
the orchestration can be exercised end to end without a TalentLMS
account: every method records the would-be payload onto self.recorded
and returns a deterministic stub response.

TalentLMS endpoint naming is verb-ish (POST /coursecreate, POST
/createunit, etc.) rather than the resource-y shape Canvas and Thinkific
use. The sync orchestrator does not care; it only calls the methods on
this client.
"""

import logging
import time
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

DEFAULT_RETRY_COUNT = 3
DEFAULT_BACKOFF_BASE = 2.0  # seconds


class TalentLMSError(Exception):
    """Raised when the TalentLMS API returns an error we cannot recover from."""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class TalentLMSClient:
    """Minimal TalentLMS API client for course content sync."""

    def __init__(self, api_url: str, api_key: str, dry_run: bool = False):
        if not dry_run:
            if not api_key or api_key.startswith("your_"):
                raise TalentLMSError(
                    "TALENTLMS_API_KEY is missing or still a placeholder."
                )
            if not api_url or api_url.startswith("https://your-"):
                raise TalentLMSError(
                    "TALENTLMS_API_URL is missing or still a placeholder."
                )

        # Normalize: strip trailing slash, ensure /api/v1 suffix.
        api_url = (api_url or "https://example.talentlms.com").rstrip("/")
        if not api_url.endswith("/api/v1"):
            api_url = api_url + "/api/v1"
        self.api_url = api_url
        self.api_key = api_key
        self.dry_run = dry_run

        parsed = urlparse(api_url)
        self.host = parsed.netloc or "example.talentlms.com"

        self._next_id = 1000
        self.recorded: list[dict] = []

        if not dry_run:
            self.session = requests.Session()
            # TalentLMS auth: HTTP Basic with API key as username, anything
            # for password. Empty password works on the public docs samples.
            self.session.auth = (api_key, "")
            self.session.headers.update({"Accept": "application/json"})
        else:
            self.session = None

    # ---- dry-run helpers ---------------------------------------------------

    def _next_dry_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def _record(self, method: str, path: str, **kwargs):
        entry = {"method": method, "path": path}
        if "json" in kwargs:
            entry["json"] = kwargs["json"]
        if "data" in kwargs:
            entry["data"] = kwargs["data"]
        if "params" in kwargs:
            entry["params"] = kwargs["params"]
        self.recorded.append(entry)

    def _dry_response(self, method: str, path: str, **kwargs) -> dict:
        if method == "GET":
            if "coursestatus" in path:
                return {
                    "id": kwargs.get("params", {}).get("course_id")
                          or self._next_dry_id()
                }
            return {}
        body = kwargs.get("json") or kwargs.get("data") or {}
        stub: dict = {"id": self._next_dry_id()}
        for key in ("name", "description", "course_id", "type", "category_id",
                    "test_id"):
            if isinstance(body, dict) and key in body:
                stub[key] = body[key]
        return stub

    # ---- core request ------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make a request with retry on transient failures. Honors dry_run.

        TalentLMS POST endpoints expect form-encoded bodies, not JSON. The
        callers here pass `data=...` for POST bodies and `params=...` for
        GET query strings.
        """
        self._record(method, path, **kwargs)

        if self.dry_run:
            return self._dry_response(method, path, **kwargs)

        url = f"{self.api_url}{path}"

        for attempt in range(DEFAULT_RETRY_COUNT):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)

                if 200 <= response.status_code < 300:
                    if response.text:
                        try:
                            return response.json()
                        except ValueError:
                            return {"raw": response.text}
                    return {}

                if response.status_code == 429:
                    retry_after = int(response.headers.get(
                        "Retry-After", DEFAULT_BACKOFF_BASE * (attempt + 1)
                    ))
                    logger.warning(
                        f"Rate limited. Sleeping {retry_after}s before retry."
                    )
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    backoff = DEFAULT_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        f"Server error {response.status_code}. Sleeping {backoff}s."
                    )
                    time.sleep(backoff)
                    continue

                raise TalentLMSError(
                    f"API error {response.status_code} on {method} {path}",
                    status_code=response.status_code,
                    response_body=response.text[:500],
                )

            except requests.RequestException as e:
                if attempt == DEFAULT_RETRY_COUNT - 1:
                    raise TalentLMSError(f"Network error on {method} {path}: {e}")
                backoff = DEFAULT_BACKOFF_BASE * (2 ** attempt)
                logger.warning(f"Network error. Sleeping {backoff}s.")
                time.sleep(backoff)

        raise TalentLMSError(f"Exhausted retries on {method} {path}")

    # ---- public methods ----------------------------------------------------

    def test_auth(self) -> bool:
        """Verify the API credentials work."""
        if self.dry_run:
            self._record("GET", "/users/id:1")
            return True
        try:
            self._request("GET", "/users/id:1")
            return True
        except TalentLMSError as e:
            if e.status_code in (401, 403):
                return False
            # 404 etc. is OK; auth worked, the user just isn't there.
            return True

    def course_status(self, course_id: int) -> dict:
        """GET /coursestatus?course_id=NN — read existing course state."""
        return self._request("GET", "/coursestatus",
                              params={"course_id": course_id})

    def create_course(self, name: str, description: str = "",
                       category_id: Optional[int] = None) -> dict:
        """POST /coursecreate — create a course."""
        body = {"name": name, "description": description}
        if category_id is not None:
            body["category_id"] = int(category_id)
        return self._request("POST", "/coursecreate", data=body)

    def create_course_category(self, name: str,
                                price: Optional[str] = None) -> dict:
        """POST /createcoursecategory — organize courses under a category."""
        body = {"name": name}
        if price is not None:
            body["price"] = price
        return self._request("POST", "/createcoursecategory", data=body)

    def add_to_course_category(self, course_id: int,
                                 category_id: int) -> dict:
        """POST /addtocoursecategory — attach a course to a category."""
        return self._request("POST", "/addtocoursecategory", data={
            "course_id": course_id,
            "category_id": category_id,
        })

    def create_unit(self, course_id: int, name: str,
                     unit_type: str = "text",
                     description: str = "") -> dict:
        """POST /createunit — create a unit (lesson, section header, etc.).

        unit_type values include text, web, link, document, video, audio,
        scorm, exam. The sync orchestrator uses 'web' for HTML lesson
        bodies and 'text' for section header units.
        """
        body: dict = {
            "course_id": course_id,
            "name": name,
            "type": unit_type,
        }
        if description:
            body["description"] = description
        return self._request("POST", "/createunit", data=body)

    def create_unit_file(self, unit_id: int, content_html: str) -> dict:
        """POST /createunitfile — attach HTML content to a unit.

        TalentLMS treats the unit body as a file payload. The HTML lesson
        body is uploaded here after the unit is created via /createunit.
        """
        return self._request("POST", "/createunitfile", data={
            "unit_id": unit_id,
            "content": content_html,
        })

    def create_course_test(self, course_id: int, name: str,
                            description: str = "",
                            pass_score: Optional[int] = None,
                            shuffle_questions: bool = True,
                            shuffle_answers: bool = True,
                            max_attempts: Optional[int] = None) -> dict:
        """POST /createcoursetest — create a test (quiz) inside a course.

        pass_score is an integer percentage (0-100). Phase 14 fields
        max_attempts and shuffle_* are passed through where supported.
        """
        body: dict = {
            "course_id": course_id,
            "name": name,
            "description": description,
            "shuffle_questions": int(bool(shuffle_questions)),
            "shuffle_answers": int(bool(shuffle_answers)),
        }
        if pass_score is not None:
            body["pass_score"] = int(pass_score)
        if max_attempts is not None:
            body["max_attempts"] = int(max_attempts)
        return self._request("POST", "/createcoursetest", data=body)

    def create_test_question(self, test_id: int, question_text: str,
                              choices: list[dict],
                              question_type: str = "multiple_choice",
                              explanation: str = "") -> dict:
        """POST /createtestquestion — add a question to a test.

        choices follows the same shape Canvas and Thinkific expect:
            [{"text": str, "correct": bool}, ...]

        TalentLMS wants answer fields named answer1..answerN with
        correct_answer indicating which one is correct (1-based index).
        """
        body: dict = {
            "test_id": test_id,
            "type": question_type,
            "question": question_text,
        }
        correct_indices = []
        for i, choice in enumerate(choices, start=1):
            body[f"answer{i}"] = choice.get("text", "")
            if choice.get("correct"):
                correct_indices.append(i)
        if correct_indices:
            body["correct_answer"] = correct_indices[0]
        if explanation:
            body["explanation"] = explanation
        return self._request("POST", "/createtestquestion", data=body)

    def admin_url_for_course(self, course_id: int) -> str:
        """Return the admin URL for a course on the TalentLMS domain."""
        return f"https://{self.host}/admin/courses/id:{course_id}".replace(
            "/api/v1", ""
        )
