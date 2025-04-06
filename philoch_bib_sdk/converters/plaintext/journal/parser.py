import traceback
from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger, remove_extra_whitespace
from philoch_bib_sdk.logic.models import Journal, BibStringAttr, TBibString

lgr = get_logger(__name__)


def parse_journal(text: str, bibstring_type: TBibString) -> Ok[Journal | None] | Err:
    """
    Parse a journal string into a Journal object.
    """
    try:
        if text == "":
            lgr.debug("Empty journal string, returning None.")
            return Ok(None)

        # Normalize the text by removing extra whitespace
        normalized_text = remove_extra_whitespace(text)

        journal = Journal(
            name=BibStringAttr(**{str(bibstring_type): normalized_text}),
            issn_electronic="",
            issn_print="",
        )

        return Ok(journal)

    except Exception as e:
        error_message = f"Error parsing journal string '{text}': {e}"
        return Err(
            message=error_message,
            code=-1,
            error_type=f"{e.__class__.__name__}",
            error_trace=traceback.format_exc(),
        )
