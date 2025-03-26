import traceback
from typing import Tuple
from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger, remove_extra_whitespace
from philoch_bib_sdk.logic.models import Author

lgr = get_logger(__name__)


def _parse_normalize(text: str) -> Tuple[str, str]:
    """
    Return a tuple of two strings, the first of which is the given name, and the second of which is the family name. If only one name is found, the second string will be empty.

    Fails if more than two names are found.
    """
    parts = tuple(remove_extra_whitespace(part) for part in text.split(","))

    if len(parts) > 2:
        raise ValueError(f"Unexpected number of author parts found in '{text}': '{parts}'. Expected 2 or less.")

    elif len(parts) == 0:
        return ("", "")

    elif len(parts) == 1:
        # Mononym
        return (parts[0], "")

    else:
        # Full name
        return (parts[1], parts[0])


def parse_author(text: str, latex: bool = False) -> Ok[Tuple[Author, ...]] | Err:
    """
    Return either a string, or a parsing error.
    """
    try:
        if text == "":
            return Ok(())

        parts = tuple(remove_extra_whitespace(part) for part in text.split("and"))
        parts_normalized = tuple(_parse_normalize(part) for part in parts)

        authors = tuple(
            Author(
                given_name=part[0] if not latex else "",
                family_name=part[1] if not latex else "",
                given_name_latex=part[0] if latex else "",
                family_name_latex=part[1] if latex else "",
            )
            for part in parts_normalized
        )

        return Ok(authors)

    except Exception as e:
        return Err(
            message=f"Could not parse 'author' field with value [[ {text} ]]. {e.__class__.__name__}: {e}",
            code=-1,
            error_type="ParsingError",
            error_trace=f"{traceback.format_exc()}",
        )
