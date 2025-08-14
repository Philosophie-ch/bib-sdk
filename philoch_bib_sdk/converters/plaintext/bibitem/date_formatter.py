from typing import Literal
from philoch_bib_sdk.logic.models import VALID_DATE_FORMATS, BibItemDateAttr


def format_date(date: BibItemDateAttr | Literal["no date"]) -> str:

    if date == "no date":
        return "no date"

    match date:
        case BibItemDateAttr(year=year, year_part_2_hyphen=None, year_part_2_slash=None, month=None, day=None):
            return str(year)

        case BibItemDateAttr(year=year, year_part_2_hyphen=None, year_part_2_slash=None, month=month, day=day) if (
            month is not None and day is not None
        ):
            return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"

        case BibItemDateAttr(year=year, year_part_2_hyphen=None, year_part_2_slash=None, month=month, day=None) if (
            month is not None
        ):
            return f"{year}-{str(month).zfill(2)}"

        case BibItemDateAttr(
            year=year, year_part_2_hyphen=year_part_2_hyphen, year_part_2_slash=None, month=None, day=None
        ) if (year_part_2_hyphen is not None):
            return f"{year}-{year_part_2_hyphen}"

        case BibItemDateAttr(
            year=year, year_part_2_hyphen=None, year_part_2_slash=year_part_2_slash, month=None, day=None
        ) if (year_part_2_slash is not None):
            return f"{year}/{year_part_2_slash}"

        case _:
            raise ValueError(
                f"Invalid date format. Expected one of {', '.join(VALID_DATE_FORMATS)}, but found '{date}'."
            )
