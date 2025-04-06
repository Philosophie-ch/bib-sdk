from typing import Literal
from philoch_bib_sdk.logic.models import VALID_DATE_FORMATS, BibItemDateAttr


def format_date(date: BibItemDateAttr | Literal["no date"]) -> str:

    if date == "no date":
        return "no date"

    match (date.year, date.year_part_2_hyphen, date.year_part_2_slash, date.month, date.day):
        case (year, "", "", "", ""):
            return str(year)

        case (year, "", "", month, day):
            return f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"

        case (year, year_part_2_hyphens, "", "", ""):
            return f"{year}-{year_part_2_hyphens}"

        case (year, "", year_part_2_slash, "", ""):
            return f"{year}/{year_part_2_slash}"

        case _:
            raise ValueError(
                f"Invalid date format. Expected oue of {", ".join(VALID_DATE_FORMATS)}, but found '{date}'."
            )
