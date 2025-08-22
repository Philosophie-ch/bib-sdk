from typing import Callable, Dict, Tuple
from philoch_bib_sdk.converters.plaintext.journal.formatter import format_journal
from philoch_bib_sdk.logic.models import BibItem, BibKeyAttr


type TJournalName = str

type TVolume = str

type TNumber = str

type TBibkey = str


type TJournalBibkeyIndex = Dict[
    Tuple[TJournalName, TVolume, TNumber], BibKeyAttr
]  # (journal, volume, number)  # bibkey


def get_bibkey_by_journal_volume_number(index: TJournalBibkeyIndex, subject: BibItem) -> BibKeyAttr:
    """
    Simple lookup of a Bibitem on an index for its bibkey, via the combination (journal_name, volume, number). Fails if any of the three fields are missing.
    """

    journal = format_journal(subject.journal, bibstring_type="latex")
    volume = subject.volume
    number = subject.number

    if any((journal == "", volume == "", number == "")):
        raise ValueError(
            f"Expected subject bibitem journal with non-empty journal, volume, and number. Found [[ journal: {journal}; volume: {volume}; number: {number} ]] instead."
        )

    return index[(journal, volume, number)]


type TReadIndex = Callable[
    [
        str,  # path to the index file
    ],
    TJournalBibkeyIndex,
]
