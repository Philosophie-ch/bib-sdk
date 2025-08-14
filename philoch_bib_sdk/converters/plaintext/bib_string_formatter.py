from philoch_bib_sdk.logic.models import BibStringAttr, MaybeStr, TBibString


def format_bib_string_attr(bib_string: MaybeStr[BibStringAttr], bibstring_type: TBibString) -> str:
    """
    Format a BibStringAttr into a string representation.
    """
    return "" if not bib_string else getattr(bib_string, bibstring_type, "")
