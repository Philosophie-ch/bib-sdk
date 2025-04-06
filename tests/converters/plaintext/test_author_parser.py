from aletk.ResultMonad import Ok, Err
from philoch_bib_sdk.converters.plaintext.author.parser import parse_author


def test_author_parse() -> None:

    raw_text = ""
    result = parse_author(raw_text, "simplified")

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 0

    raw_author = "Doe, John"
    result = parse_author(raw_author, "simplified")

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 1
    assert output[0].given_name.simplified == "John"
    assert output[0].family_name.simplified == "Doe"
    assert output[0].mononym.simplified == ""

    raw_mononym = "Aristotle"
    result = parse_author(raw_mononym, "simplified")

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 1
    assert output[0].given_name.simplified == ""
    assert output[0].family_name.simplified == ""
    assert output[0].mononym.simplified == "Aristotle"

    # Complex case: multiple authors, some mononyms, and added whitespace
    raw_authors = " Aristotle and de  las Casas, Bartolomé and Tarski,  Alfred and Plato"
    result = parse_author(raw_authors, "simplified")

    assert isinstance(result, Ok)
    output = result.out
    assert len(output) == 4
    assert output[0].given_name.simplified == ""
    assert output[0].family_name.simplified == ""
    assert output[0].mononym.simplified == "Aristotle"
    assert output[1].given_name.simplified == "Bartolomé"
    assert output[1].family_name.simplified == "de las Casas"
    assert output[1].mononym.simplified == ""
    assert output[2].given_name.simplified == "Alfred"
    assert output[2].family_name.simplified == "Tarski"
    assert output[2].mononym.simplified == ""
    assert output[3].given_name.simplified == ""
    assert output[3].family_name.simplified == ""
    assert output[3].mononym.simplified == "Plato"


def test_author_parse_error() -> None:
    # List of authors separated by a comma, instead of just ' and '
    raw_text = "Doe, John, and Jane"
    result = parse_author(raw_text, "simplified")

    assert isinstance(result, Err)

    # List of authors with a mix of commas and ' and '
    raw_text = "Doe, John, and Jane, and Smith"
    result = parse_author(raw_text, "simplified")

    assert isinstance(result, Err)
