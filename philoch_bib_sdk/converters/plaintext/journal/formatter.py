from aletk.utils import get_logger
from philoch_bib_sdk.logic.models import Journal, TBibString

lgr = get_logger(__name__)


def format_journal(journal: Journal | None, bibstring_type: TBibString) -> str:
    """
    Format a journal object into a string representation.
    """
    if journal is None:
        return ""

    journal_name = f"{getattr(journal.name, bibstring_type)}"
    return journal_name
