from philoch_bib_sdk.logic.models import BibKeyAttr, MaybeStr


def format_bibkey(bibkey: MaybeStr[BibKeyAttr]) -> str:

    if bibkey == "":
        return ""

    if bibkey.other_authors:
        authors_l = [bibkey.first_author, bibkey.other_authors]
    else:
        authors_l = [bibkey.first_author]

    authors = "-".join(authors_l)

    if isinstance(bibkey.date, int):
        year = f"{bibkey.date}{bibkey.date_suffix}"
    else:
        year = f"{bibkey.date}-{bibkey.date_suffix}" if bibkey.date_suffix else bibkey.date

    return f"{authors}:{year}"
