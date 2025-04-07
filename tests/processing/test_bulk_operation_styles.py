from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Literal, Tuple
import cytoolz as tz
from timeit import timeit
from aletk.utils import get_logger

import pytest

from philoch_bib_sdk.logic.models import Author, BibStringAttr
from philoch_bib_sdk.converters.plaintext.author.formatter import format_author


lgr = get_logger(__name__)

type TLightweightBibItem = Tuple[Tuple[Author, ...], ...]
type TFormattedLightweightBibItem = Tuple[str, ...]

type TProcessingStyle = Literal["comprehension", "cytoolz_map", "cytoolz_concurrent"]

# Set here the current style used in the project
STYLE_USED: TProcessingStyle = "comprehension"

type TProcessingFunction = Callable[[TLightweightBibItem], TFormattedLightweightBibItem]

type TCurrFormatAuthor = Callable[[Tuple[Author, ...]], str]
curr_format_author: TCurrFormatAuthor = lambda x: format_author(x, "simplified")


def f_comprehension(input: TLightweightBibItem) -> TFormattedLightweightBibItem:
    """
    Mimick a bibitem formatter, but just the author part.
    """
    return tuple(format_author(authors, "simplified") for authors in input)


def f_cytoolz_map(input: TLightweightBibItem) -> TFormattedLightweightBibItem:
    """
    Mimick a bibitem formatter, but just the author part.
    """
    result = tuple(tz.map(curr_format_author, input))

    return result


def f_cytoolz_concurrent(input: TLightweightBibItem) -> TFormattedLightweightBibItem:
    """
    Mimick a bibitem formatter, but just the author part.
    """
    with ThreadPoolExecutor() as executor:
        formatted_bibitems = tuple(
            tz.map(lambda authors: executor.submit(format_author, authors, "simplified").result(), input)
        )
    return formatted_bibitems


@pytest.fixture
def authors_data() -> TLightweightBibItem:
    return tuple(
        tuple(
            Author(
                BibStringAttr(simplified=f"Given{i}{j}"),
                BibStringAttr(simplified=f"Family{i}{j}"),
                BibStringAttr(simplified=f"Mononym{i}{j}"),
                BibStringAttr(simplified=f"Shorthand{i}{j}"),
                BibStringAttr(simplified=f"FamousName{i}{j}"),
                (),
            )
            for j in range(3)
        )
        for i in range(1000)
    )


@pytest.mark.experimental
def test_comprehension_vs_cytoolz_concurrent(authors_data: TLightweightBibItem) -> None:
    """
    Compare the performance of comprehension and cytoolz.
    """

    # Warm up
    f_comprehension(authors_data)
    f_cytoolz_map(authors_data)
    f_cytoolz_concurrent(authors_data)

    functions: Dict[TProcessingStyle, TProcessingFunction] = {
        "comprehension": f_comprehension,
        "cytoolz_map": f_cytoolz_map,
        "cytoolz_concurrent": f_cytoolz_concurrent,
    }
    results: Dict[TProcessingStyle, float] = {}

    # Benchmark
    function_outputs: Dict[TProcessingStyle, TFormattedLightweightBibItem] = {}
    for style, f in functions.items():

        time = timeit(
            lambda: function_outputs.setdefault(style, f(authors_data)),
            number=1000,
        )
        results[style] = time

    # Print results
    comprehension_output = function_outputs["comprehension"]
    cytoolz_map_output = function_outputs["cytoolz_map"]
    cytoolz_concurrent_output = function_outputs["cytoolz_concurrent"]

    lgr.info(f"Comprehension outputted {len(comprehension_output)} items. Sample: {comprehension_output[:1]}")
    lgr.info(f"Cytoolz map outputted {len(cytoolz_map_output)} items. Sample: {cytoolz_map_output[:1]}")
    lgr.info(
        f"Cytoolz concurrent outputted {len(cytoolz_concurrent_output)} items. Sample: {cytoolz_concurrent_output[:1]}"
    )

    comprehension_time = results["comprehension"]
    cytoolz_map_time = results["cytoolz_map"]
    cytoolz_concurrent_time = results["cytoolz_concurrent"]

    print("")
    lgr.info(f"Comprehension time: {comprehension_time:.2f} seconds")
    lgr.info(f"Cytoolz map time: {cytoolz_map_time:.2f} seconds")
    lgr.info(f"Cytoolz concurrent time: {cytoolz_concurrent_time:.2f} seconds")

    # Check that you're using the most performant one
    sorted_results = sorted(results.items(), key=lambda x: x[1])
    best_style = sorted_results[0][0]

    # assert best_style == STYLE_USED, f"Expected {STYLE_USED}, but got {best_style}. Please update the code to ensure better performance."
