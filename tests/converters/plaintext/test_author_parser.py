from aletk.ResultMonad import Ok, Err
from philoch_bib_sdk.converters.plaintext.author.parser import parse_author
from philoch_bib_sdk.logic.models import Author


def test_author_parse() -> None:

    raw_text = ""
    result = parse_author(raw_text)

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 0

    raw_author = "Doe, John"
    result = parse_author(raw_author)

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 1
    assert output[0] == Author("John", "Doe")

    raw_mononym = "Aristotle"
    result = parse_author(raw_mononym)

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 1
    assert output[0] == Author("Aristotle")

    # Complex case: multiple authors, some mononyms, and added whitespace
    raw_authors = " Aristotle and de  las Casas, Bartolomé and Tarski,  Alfred and Plato"
    result = parse_author(raw_authors)

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 4
    assert output[0] == Author("Aristotle")
    assert output[1] == Author("Bartolomé", "de las Casas")
    assert output[2] == Author("Alfred", "Tarski")
    assert output[3] == Author("Plato")


def test_author_parse_error() -> None:
    raw_text = "Doe, John, and Jane"
    result = parse_author(raw_text)

    assert isinstance(result, Err)

    raw_text = "Doe, John, and Jane, and Smith"
    result = parse_author(raw_text)

    assert isinstance(result, Err)
