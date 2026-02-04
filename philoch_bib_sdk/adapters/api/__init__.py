"""HTTP API adapter for the Rust Bibliography API.

This module provides an HTTP client for interacting with the Rust API,
handling authentication, error responses, and entity creation.
"""

from types import TracebackType
from typing import Dict, Literal, Mapping

import attrs
import httpx

# JSON types at the HTTP boundary: httpx.Response.json() returns untyped data
# and request payloads contain heterogeneous values. Using object since
# the structure is validated at runtime by checking specific keys.
_JsonDict = Dict[str, object]

from aletk.ResultMonad import Err, Ok
from aletk.utils import get_logger

from philoch_bib_sdk.converters.api import (
    ApiAuthor,
    ApiBibItem,
    ApiInstitution,
    ApiJournal,
    ApiPublisher,
    ApiSchool,
    ApiSeries,
)

lgr = get_logger(__name__)

__all__: list[str] = [
    "ApiClient",
    "ApiError",
]


class ApiError(Exception):
    """Exception raised for API errors."""

    def __init__(self, status_code: int, message: str, response_body: str = "") -> None:
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"API Error {status_code}: {message}")


@attrs.define
class ApiClient:
    """HTTP client for the Rust Bibliography API.

    This client handles authentication and provides methods for creating
    entities in the API. It uses the get-or-create pattern, handling
    409 Conflict responses by fetching the existing entity.
    """

    base_url: str
    api_key: str
    timeout: float = 30.0
    _client: httpx.Client = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        """Initialize the HTTP client with auth headers."""
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        json: Mapping[str, object] | None = None,
    ) -> Ok[_JsonDict] | Err:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/authors")
            json: JSON body for POST/PUT requests

        Returns:
            Ok with response JSON or Err with error details
        """
        try:
            response = self._client.request(method, path, json=json)

            if response.status_code >= 400:
                try:
                    error_body: _JsonDict = response.json()
                    error_inner = error_body.get("error")
                    if isinstance(error_inner, dict):
                        error_msg = str(error_inner.get("message", response.text))
                    else:
                        error_msg = response.text
                except Exception:
                    error_msg = response.text

                return Err(
                    message=f"API {method} {path} failed: {response.status_code} - {error_msg}",
                    code=response.status_code,
                    error_type="ApiError",
                )

            if response.status_code == 204:
                return Ok({})

            response_data: _JsonDict = response.json()
            return Ok(response_data)

        except httpx.RequestError as e:
            return Err(
                message=f"HTTP request failed: {e}",
                code=-1,
                error_type="HttpError",
            )

    def _extract_id(self, result: Ok[_JsonDict]) -> Ok[int] | Err:
        """Extract integer 'id' from a successful API response.

        Args:
            result: Ok result containing response JSON

        Returns:
            Ok with the integer ID, or Err if 'id' is not an integer
        """
        id_value = result.out.get("id")
        if isinstance(id_value, int):
            return Ok(id_value)
        return Err(
            message=f"Unexpected response: expected integer 'id', got {type(id_value).__name__}",
            code=-1,
            error_type="ApiError",
        )

    # =========================================================================
    # Author operations
    # =========================================================================

    def create_author(self, author: ApiAuthor) -> Ok[int] | Err:
        """Create an author in the API.

        Args:
            author: ApiAuthor object to create

        Returns:
            Ok with the created author ID, or Err on failure
        """
        # NOTE: The database has a CHECK constraint that requires
        # family_name_latex OR mononym_latex to be NOT NULL.
        # Empty strings satisfy NOT NULL, so we MUST send all name fields.
        payload = {
            "author_key": author.author_key,
            "family_name_latex": author.family_name_latex or "",
            "family_name_unicode": author.family_name_unicode or "",
            "family_name_simplified": author.family_name_simplified or "",
            "given_name_latex": author.given_name_latex or "",
            "given_name_unicode": author.given_name_unicode or "",
            "given_name_simplified": author.given_name_simplified or "",
            "mononym_latex": author.mononym_latex or "",
            "mononym_unicode": author.mononym_unicode or "",
            "mononym_simplified": author.mononym_simplified or "",
        }

        result = self._request("POST", "/authors", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_author_by_key(self, author_key: str) -> Ok[_JsonDict] | Err:
        """Get an author by their key.

        Args:
            author_key: The author's unique key

        Returns:
            Ok with author data or Err if not found
        """
        # The API might have a by-key endpoint, or we search
        result = self._request("GET", f"/authors/by-key/{author_key}")
        return result

    def get_or_create_author(self, author: ApiAuthor) -> Ok[int] | Err:
        """Create an author or get existing one if duplicate.

        Args:
            author: ApiAuthor object

        Returns:
            Ok with author ID (new or existing)
        """
        result = self.create_author(author)
        if isinstance(result, Ok):
            lgr.debug(f"Created author: {author.author_key} -> ID {result.out}")
            return result

        # Check if it's a duplicate (409 Conflict)
        if result.code == 409:
            lgr.debug(f"Author already exists: {author.author_key}, fetching...")
            existing = self.get_author_by_key(author.author_key)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # Journal operations
    # =========================================================================

    def create_journal(self, journal: ApiJournal) -> Ok[int] | Err:
        """Create a journal in the API."""
        payload = {
            "journal_key": journal.journal_key,
            "name_latex": journal.name_latex,
            "name_unicode": journal.name_unicode,
            "name_simplified": journal.name_simplified,
            "issn_print": journal.issn_print,
            "issn_electronic": journal.issn_electronic,
        }
        payload = {k: v for k, v in payload.items() if v}

        result = self._request("POST", "/journals", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_journal_by_key(self, journal_key: str) -> Ok[_JsonDict] | Err:
        """Get a journal by its key."""
        return self._request("GET", f"/journals/by-key/{journal_key}")

    def get_or_create_journal(self, journal: ApiJournal) -> Ok[int] | Err:
        """Create a journal or get existing one if duplicate."""
        result = self.create_journal(journal)
        if isinstance(result, Ok):
            lgr.debug(f"Created journal: {journal.journal_key} -> ID {result.out}")
            return result

        if result.code == 409:
            lgr.debug(f"Journal already exists: {journal.journal_key}, fetching...")
            existing = self.get_journal_by_key(journal.journal_key)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # Publisher operations
    # =========================================================================

    def create_publisher(self, publisher: ApiPublisher) -> Ok[int] | Err:
        """Create a publisher in the API."""
        payload = {
            "publisher_key": publisher.publisher_key,
            "name_latex": publisher.name_latex,
            "name_unicode": publisher.name_unicode,
            "name_simplified": publisher.name_simplified,
            "default_address": publisher.default_address,
        }
        payload = {k: v for k, v in payload.items() if v}

        result = self._request("POST", "/publishers", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_publisher_by_key(self, publisher_key: str) -> Ok[_JsonDict] | Err:
        """Get a publisher by its key."""
        return self._request("GET", f"/publishers/by-key/{publisher_key}")

    def get_or_create_publisher(self, publisher: ApiPublisher) -> Ok[int] | Err:
        """Create a publisher or get existing one if duplicate."""
        result = self.create_publisher(publisher)
        if isinstance(result, Ok):
            lgr.debug(f"Created publisher: {publisher.publisher_key} -> ID {result.out}")
            return result

        if result.code == 409:
            lgr.debug(f"Publisher already exists: {publisher.publisher_key}, fetching...")
            existing = self.get_publisher_by_key(publisher.publisher_key)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # Institution operations
    # =========================================================================

    def create_institution(self, institution: ApiInstitution) -> Ok[int] | Err:
        """Create an institution in the API."""
        payload = {
            "institution_key": institution.institution_key,
            "name_latex": institution.name_latex,
            "name_unicode": institution.name_unicode,
            "name_simplified": institution.name_simplified,
        }
        payload = {k: v for k, v in payload.items() if v}

        result = self._request("POST", "/institutions", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_institution_by_key(self, institution_key: str) -> Ok[_JsonDict] | Err:
        """Get an institution by its key."""
        return self._request("GET", f"/institutions/by-key/{institution_key}")

    def get_or_create_institution(self, institution: ApiInstitution) -> Ok[int] | Err:
        """Create an institution or get existing one if duplicate."""
        result = self.create_institution(institution)
        if isinstance(result, Ok):
            lgr.debug(f"Created institution: {institution.institution_key} -> ID {result.out}")
            return result

        if result.code == 409:
            existing = self.get_institution_by_key(institution.institution_key)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # School operations
    # =========================================================================

    def create_school(self, school: ApiSchool) -> Ok[int] | Err:
        """Create a school in the API."""
        payload = {
            "school_key": school.school_key,
            "name_latex": school.name_latex,
            "name_unicode": school.name_unicode,
            "name_simplified": school.name_simplified,
        }
        payload = {k: v for k, v in payload.items() if v}

        result = self._request("POST", "/schools", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_school_by_key(self, school_key: str) -> Ok[_JsonDict] | Err:
        """Get a school by its key."""
        return self._request("GET", f"/schools/by-key/{school_key}")

    def get_or_create_school(self, school: ApiSchool) -> Ok[int] | Err:
        """Create a school or get existing one if duplicate."""
        result = self.create_school(school)
        if isinstance(result, Ok):
            lgr.debug(f"Created school: {school.school_key} -> ID {result.out}")
            return result

        if result.code == 409:
            existing = self.get_school_by_key(school.school_key)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # Series operations
    # =========================================================================

    def create_series(self, series: ApiSeries) -> Ok[int] | Err:
        """Create a series in the API."""
        payload = {
            "series_key": series.series_key,
            "name_latex": series.name_latex,
            "name_unicode": series.name_unicode,
            "name_simplified": series.name_simplified,
        }
        payload = {k: v for k, v in payload.items() if v}

        result = self._request("POST", "/series", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_series_by_key(self, series_key: str) -> Ok[_JsonDict] | Err:
        """Get a series by its key."""
        return self._request("GET", f"/series/by-key/{series_key}")

    def get_or_create_series(self, series: ApiSeries) -> Ok[int] | Err:
        """Create a series or get existing one if duplicate."""
        result = self.create_series(series)
        if isinstance(result, Ok):
            lgr.debug(f"Created series: {series.series_key} -> ID {result.out}")
            return result

        if result.code == 409:
            existing = self.get_series_by_key(series.series_key)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # BibItem operations
    # =========================================================================

    def create_bibitem(self, bibitem: ApiBibItem) -> Ok[int] | Err:
        """Create a bibitem in the API."""
        payload: _JsonDict = {
            "bibkey": bibitem.bibkey,
        }

        # Add optional fields if present
        if bibitem.entry_type:
            payload["entry_type"] = bibitem.entry_type
        if bibitem.pubstate:
            payload["pubstate"] = bibitem.pubstate

        # Title fields
        if bibitem.title_latex:
            payload["title_latex"] = bibitem.title_latex
        if bibitem.title_unicode:
            payload["title_unicode"] = bibitem.title_unicode
        if bibitem.title_simplified:
            payload["title_simplified"] = bibitem.title_simplified

        # Booktitle fields
        if bibitem.booktitle_latex:
            payload["booktitle_latex"] = bibitem.booktitle_latex
        if bibitem.booktitle_unicode:
            payload["booktitle_unicode"] = bibitem.booktitle_unicode
        if bibitem.booktitle_simplified:
            payload["booktitle_simplified"] = bibitem.booktitle_simplified

        # Date fields
        if bibitem.date_year is not None:
            payload["date_year"] = bibitem.date_year
        if bibitem.date_year_2_hyphen is not None:
            payload["date_year_2_hyphen"] = bibitem.date_year_2_hyphen
        if bibitem.date_year_2_slash is not None:
            payload["date_year_2_slash"] = bibitem.date_year_2_slash
        if bibitem.date_month is not None:
            payload["date_month"] = bibitem.date_month
        if bibitem.date_day is not None:
            payload["date_day"] = bibitem.date_day
        if bibitem.date_is_no_date:
            payload["date_is_no_date"] = True

        # Entity IDs
        if bibitem.journal_id is not None:
            payload["journal_id"] = bibitem.journal_id
        if bibitem.publisher_id is not None:
            payload["publisher_id"] = bibitem.publisher_id
        if bibitem.institution_id is not None:
            payload["institution_id"] = bibitem.institution_id
        if bibitem.school_id is not None:
            payload["school_id"] = bibitem.school_id
        if bibitem.series_id is not None:
            payload["series_id"] = bibitem.series_id
        if bibitem.person_id is not None:
            payload["person_id"] = bibitem.person_id

        # Simple fields
        if bibitem.volume:
            payload["volume"] = bibitem.volume
        if bibitem.number:
            payload["number"] = bibitem.number
        if bibitem.pages:
            payload["pages"] = bibitem.pages
        if bibitem.eid:
            payload["eid"] = bibitem.eid
        if bibitem.edition:
            payload["edition"] = bibitem.edition
        if bibitem.address:
            payload["address"] = bibitem.address
        if bibitem.type_field:
            payload["type_field"] = bibitem.type_field

        # Identifiers
        if bibitem.doi:
            payload["doi"] = bibitem.doi
        if bibitem.url:
            payload["url"] = bibitem.url
        if bibitem.urn:
            payload["urn"] = bibitem.urn
        if bibitem.eprint:
            payload["eprint"] = bibitem.eprint

        # Crossref
        if bibitem.crossref_bibkey:
            payload["crossref_bibkey"] = bibitem.crossref_bibkey

        # Issue and notes
        if bibitem.issuetitle_latex:
            payload["issuetitle_latex"] = bibitem.issuetitle_latex
        if bibitem.issuetitle_unicode:
            payload["issuetitle_unicode"] = bibitem.issuetitle_unicode
        if bibitem.note_latex:
            payload["note_latex"] = bibitem.note_latex
        if bibitem.note_unicode:
            payload["note_unicode"] = bibitem.note_unicode
        if bibitem.extra_note_latex:
            payload["extra_note_latex"] = bibitem.extra_note_latex
        if bibitem.extra_note_unicode:
            payload["extra_note_unicode"] = bibitem.extra_note_unicode

        # Enums
        if bibitem.langid:
            payload["langid"] = bibitem.langid
        if bibitem.epoch:
            payload["epoch"] = bibitem.epoch

        # Other
        if bibitem.options:
            payload["options"] = bibitem.options
        if bibitem.shorthand:
            payload["shorthand"] = bibitem.shorthand

        result = self._request("POST", "/bibitems", json=payload)
        if isinstance(result, Err):
            return result

        return self._extract_id(result)

    def get_bibitem_by_bibkey(self, bibkey: str) -> Ok[_JsonDict] | Err:
        """Get a bibitem by its bibkey."""
        return self._request("GET", f"/bibitems/by-bibkey/{bibkey}")

    def get_or_create_bibitem(self, bibitem: ApiBibItem) -> Ok[int] | Err:
        """Create a bibitem or get existing one if duplicate."""
        result = self.create_bibitem(bibitem)
        if isinstance(result, Ok):
            lgr.debug(f"Created bibitem: {bibitem.bibkey} -> ID {result.out}")
            return result

        if result.code == 409:
            lgr.debug(f"BibItem already exists: {bibitem.bibkey}, fetching...")
            existing = self.get_bibitem_by_bibkey(bibitem.bibkey)
            if isinstance(existing, Ok):
                return self._extract_id(existing)
            return existing

        return result

    # =========================================================================
    # BibItem-Author link operations
    # =========================================================================

    def add_bibitem_author(
        self,
        bibitem_id: int,
        author_id: int,
        role: Literal["author", "editor", "guesteditor"],
        position: int,
    ) -> Ok[None] | Err:
        """Add an author link to a bibitem.

        Args:
            bibitem_id: The ID of the bibitem
            author_id: The ID of the author
            role: The role of the author ("author", "editor", "guesteditor")
            position: The position/order of this author (1-indexed)

        Returns:
            Ok on success, Err on failure
        """
        payload = {
            "author_id": author_id,
            "role": role,
            "position": position,
        }

        result = self._request("POST", f"/bibitems/{bibitem_id}/authors", json=payload)
        if isinstance(result, Err):
            # If it's a duplicate, that's okay - link already exists
            if result.code == 409:
                lgr.debug(f"Author link already exists: bibitem={bibitem_id}, author={author_id}")
                return Ok(None)
            return result

        return Ok(None)

    # =========================================================================
    # BibItem-Keyword operations
    # =========================================================================

    def set_bibitem_keywords(
        self,
        bibitem_id: int,
        keyword_level_1_id: int | None,
        keyword_level_2_id: int | None,
        keyword_level_3_id: int | None,
    ) -> Ok[None] | Err:
        """Set keywords for a bibitem.

        Args:
            bibitem_id: The ID of the bibitem
            keyword_level_1_id: ID of level 1 keyword (or None)
            keyword_level_2_id: ID of level 2 keyword (or None)
            keyword_level_3_id: ID of level 3 keyword (or None)

        Returns:
            Ok on success, Err on failure
        """
        payload: _JsonDict = {}
        if keyword_level_1_id is not None:
            payload["keyword_level_1_id"] = keyword_level_1_id
        if keyword_level_2_id is not None:
            payload["keyword_level_2_id"] = keyword_level_2_id
        if keyword_level_3_id is not None:
            payload["keyword_level_3_id"] = keyword_level_3_id

        if not payload:
            return Ok(None)

        result = self._request("POST", f"/bibitems/{bibitem_id}/keywords", json=payload)
        if isinstance(result, Err):
            return result

        return Ok(None)
