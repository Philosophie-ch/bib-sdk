import traceback
from typing import Tuple
from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger, remove_extra_whitespace
from philoch_bib_sdk.logic.models import Author, BibKey

lgr = get_logger(__name__)


def _author_parse_normalize(text: str) -> Tuple[str, str]:
    """
    Return a tuple of two strings, the first of which is the given name, and the second of which is the family name. If only one name is found, the second string will be empty.

    Fails if more than two names are found.
    """
    parts = text.split(",")

    if len(parts) > 2:
        raise ValueError(f"Unexpected number of author parts found in '{text}': '{parts}'. Expected 2 or less.")

    elif len(parts) == 0:
        return ("", "")

    elif len(parts) == 1:
        return (parts[0], "")

    else:
        return (parts[0], parts[1])


def author_parse(text: str, latex: bool) -> Ok[Tuple[Author, ...]] | Err:
    """
    Return either a string, or a parsing error.
    """
    try:
        if text == "":
            return Ok(())

        parts = remove_extra_whitespace(text).split(" and ")
        parts_normalized = [_author_parse_normalize(part) for part in parts]

        authors = tuple(
            Author(
                given_name=author[0] if not latex else "",
                family_name=author[1] if not latex else "",
                given_name_latex=author[0] if latex else "",
                family_name_latex=author[1] if latex else "",
            )
            for author in parts_normalized
        )

        return Ok(authors)

    except Exception as e:
        return Err(
            message=f"Could not parse 'author' field with value [[ {text} ]]. {e.__class__.__name__}: {e}",
            code=-1,
            error_type="ParsingError",
            error_trace=f"{traceback.format_exc()}",
        )


def person_parse(text: str) -> Ok[Author | None] | Err:
    """
    Return either an Author object, or a parsing error.
    """
    try:
        if text == "":
            return Ok(None)

        cleaned = remove_extra_whitespace(remove_extra_whitespace(text).replace(";", ""))

        return Ok(
            Author(
                famous_name=cleaned,
            )
        )

    except Exception as e:
        return Err(
            message=f"Could not parse '_person' field with value [[ {text} ]]. {e.__class__.__name__}: {e}",
            code=-1,
            error_type="ParsingError",
            error_trace=f"{traceback.format_exc()}",
        )


def bibkey_parse(text: str, text_position_d: dict[str, int] | None = None) -> Ok[BibKey] | Err:
    """
    Return either a Bibkey object, or a BibkeyError object to indicate a parsing error.
    """

    return Err(
        message="TODO. Clean and adapt the commented out code below.",
        code=-1,
        error_type="NotImplementedError",
    )
    # try:
    # parts = text.split(":")
    # if len(parts) != 2:
    # raise ValueError(f"Unexpected number of bibkey parts for '{text}': '{parts}'")

    # author_parts = parts[0].split("-")
    # year_parts = parts[1]

    # if len(author_parts) == 1:
    # first_author = author_parts[0]
    # other_authors = None
    # elif len(author_parts) == 2:
    # first_author = author_parts[0]
    # other_authors = author_parts[1]
    # else:
    # raise ValueError(f"Unexpected bibkey author parts for '{text}': '{author_parts}'")

    # char_index_type_d = {i: (char, char.isdigit()) for i, char in enumerate(year_parts)}

    # year_l: list[str] = []
    # int_breakpoint = None
    # for value in char_index_type_d.items():
    # i, (char, is_digit) = value
    # if is_digit:
    # year_l.append(char)
    # int_breakpoint = i
    # else:
    # break

    # if year_l != []:
    # year_int = int(f"{''.join(year_l)}")
    # else:
    # year_int = None

    # if int_breakpoint is not None:
    # year_suffix = year_parts[int_breakpoint + 1 :]

    # else:
    ## all characters are non-digits
    # year_suffix = "".join(year_parts)

    # if year_suffix != "" and year_suffix not in ["unpub", "forthcoming"]:
    # if len(year_suffix) > 1:
    # if "unpub" not in year_suffix and "forthcoming" not in year_suffix:
    # lgr.warning(f"Unexpected year suffix for '{text}': '{year_suffix}'")
    # elif len(year_suffix) == 1:
    # if year_suffix.isdigit():
    # lgr.warning(f"Unexpected year suffix for '{text}': '{year_suffix}'")

    # if year_int is None and year_suffix is None:
    # raise ValueError(f"Could not parse year for '{text}': '{year_parts}'")

    # if year_int is None:
    # return Ok(Bibkey(
    # first_author=first_author,
    # year = year_int,
    # ))

    # else:
    # return Ok(
    # Bibkey(first_author=first_author, other_authors=other_authors, year=year_int, year_suffix=year_suffix)
    # )

    # except Exception as e:
    # error_message = f"Could not parse bibkey for '{text}'"

    # if text_position_d is None:
    # return Err(
    # message=f"Could not parse bibkey for '{text}'. {e.__class__.__name__}: {e}",
    # code=-1,
    # error_type="BibkeyError",
    # error_trace=f"{traceback.format_exc()}",
    # )
    # else:
    # return Err(
    # message=f"Could not parse bibkey for '{text}' at position {text_position_d}. {e.__class__}: {e}",
    # code=-1,
    # error_type="BibkeyError",
    # error_trace=f"{traceback.format_exc()}",
    # )
