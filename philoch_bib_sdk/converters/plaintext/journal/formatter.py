from aletk.utils import get_logger
from philoch_bib_sdk.logic.models import Journal, Maybe, TBibString

lgr = get_logger(__name__)


def format_journal(journal: Maybe[Journal], bibstring_type: TBibString) -> str:
    """
    Format a journal object into a string representation.
    """

    match journal:

        case None:
            return ""

        case Journal(name, id):
            value = getattr(name, bibstring_type)
            if not value:
                return ""

            return f"{value}"

        case _:
            raise TypeError(f"Invalid type for journal: {type(journal)}. Dump: {journal!r}")
