from functools import partial
from typing import Callable, NamedTuple

import polars as pl

from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_parser import hard_parse_bibkey
from philoch_bib_sdk.logic.functions.journal_article_matcher import (
    TJournalBibkeyIndex,
    TReadIndex,
)


class ColumnNames(NamedTuple):
    bibkey: str
    journal: str
    volume: str
    number: str


def _read_from_ods(
    column_names: ColumnNames,
    file_path: str,
) -> TJournalBibkeyIndex:
    """
    Reads the specified columns from an ODS file and returns a TJournalBibkeyIndex dictionary.
    Args:
        column_names (ColumnNames): The names of the columns to read (journal, volume, number, bibkey).
        file_path (str): The path to the ODS file.
    Returns:
        TJournalBibkeyIndex: A dictionary mapping (journal, volume, number) tuples to bibkey values.
    """
    df = pl.read_ods(
        source=file_path,
        has_header=True,
        columns=[column_names.journal, column_names.volume, column_names.number, column_names.bibkey],
        schema_overrides={
            column_names.journal: pl.Utf8,
            column_names.volume: pl.Utf8,
            column_names.number: pl.Utf8,
            column_names.bibkey: pl.Utf8,
        },
    )

    if df.is_empty():
        raise ValueError(
            f"Tabular data at '{file_path}' is empty or does not contain the expected columns: {column_names}"
        )

    return {
        (row[column_names.journal], row[column_names.volume], row[column_names.number]): hard_parse_bibkey(
            row[column_names.bibkey]
        )
        for row in df.to_dicts()
    }


type THOFReadFromOds = Callable[[ColumnNames], TReadIndex]
hof_read_from_ods: THOFReadFromOds = lambda column_names: partial(_read_from_ods, column_names)
