from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_parser import parse_bibkey

from aletk.ResultMonad import Ok, Err


def test_bibkey_parser() -> None:
    # Test cases for the BibKey parser
    test_cases = [
        "aristotle-etal:300a",
        "aristotle:300",
        "bordogarcia_l:forthcoming-1",
        "bordogarcia_l-olivadoti_s:2027z2",
        "bordogarcia_l-olivadoti_s:2027",
    ]

    for bibkey_str in test_cases:
        # Parse the BibKey string
        bibkey_res = parse_bibkey(bibkey_str)

        assert isinstance(bibkey_res, Ok)
        assert bibkey_str == format_bibkey(bibkey_res.out)


def test_bibkey_parser_invalid() -> None:
    # Test cases for invalid BibKey strings
    invalid_bibkeys = [
        "aristotle-etal-300a",
        "aristotle::300a",
        "bordogarcia_l:forthcoming-1-2-",
        "bordogarcia_l-olivadoti_s:-10000",
        "bordogarcia_l-olivadoti_s:10000",
        "bordogarcia_l-olivadoti_s:20241",
        "bordogarcia_l-olivadoti_s:unpub-",
        "bordogarcia_l-olivadoti_s:2027z2:3",
    ]

    for bibkey_str in invalid_bibkeys:
        # Parse the BibKey string
        bibkey_res = parse_bibkey(bibkey_str)

        assert isinstance(bibkey_res, Err)
