"""Fuzzy matching procedure for bibliographic items.

This module provides the main orchestration logic for fuzzy matching staged BibItems
against an existing bibliography. It uses dependency injection to remain agnostic
to specific IO formats (CSV, JSON, etc.).
"""

from typing import Callable, Dict, Tuple

from aletk.ResultMonad import Err, Ok, try_except_wrapper
from aletk.utils import get_logger

from philoch_bib_sdk.logic.functions.fuzzy_matcher import (
    build_index,
    stage_bibitems_batch,
)
from philoch_bib_sdk.logic.models import BibItem
from philoch_bib_sdk.logic.models_staging import BibItemStaged

logger = get_logger(__name__)

# Type aliases for dependency injection
Bibliography = Dict[str, BibItem]  # Key is formatted bibkey
LoadBibliographyFn = Callable[[str], Ok[Bibliography] | Err]
LoadStagedFn = Callable[[str], Ok[Tuple[BibItem, ...]] | Err]
WriteReportFn = Callable[[str, Tuple[BibItemStaged, ...]], Ok[None] | Err]


@try_except_wrapper(logger)
def fuzzy_match_procedure(
    bibliography_path: str,
    staged_path: str,
    output_path: str,
    load_bibliography: LoadBibliographyFn,
    load_staged: LoadStagedFn,
    write_report: WriteReportFn,
    top_n: int = 5,
    min_score: float = 0.0,
) -> Ok[None] | Err:
    """Execute fuzzy matching workflow with dependency injection.

    Args:
        bibliography_path: Path to bibliography file
        staged_path: Path to staged items file
        output_path: Path for output report (without extension)
        load_bibliography: Function to load bibliography from file
        load_staged: Function to load staged items from file
        write_report: Function to write results to file
        top_n: Number of top matches to find per item
        min_score: Minimum score threshold for matches

    Returns:
        Ok[None] on success, Err on failure
    """
    logger.info("Starting fuzzy matching procedure")
    logger.info(f"Bibliography: {bibliography_path}")
    logger.info(f"Staged items: {staged_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Parameters: top_n={top_n}, min_score={min_score}")

    # Step a: Load bibliography
    logger.info("Loading bibliography...")
    bibliography_result = load_bibliography(bibliography_path)
    if isinstance(bibliography_result, Err):
        logger.error(f"Failed to load bibliography: {bibliography_result.message}")
        return bibliography_result

    bibliography = bibliography_result.out
    logger.info(f"Loaded {len(bibliography)} items from bibliography")

    # Step b: Load staged items
    logger.info("Loading staged items...")
    staged_result = load_staged(staged_path)
    if isinstance(staged_result, Err):
        logger.error(f"Failed to load staged items: {staged_result.message}")
        return staged_result

    staged_items = staged_result.out
    logger.info(f"Loaded {len(staged_items)} staged items")

    if not staged_items:
        logger.warning("No staged items to process")
        return Ok(None)

    # Step c: Build fuzzy matching index from bibliography
    logger.info("Building fuzzy matching index...")
    try:
        # Convert dict to tuple for indexing
        bibliography_tuple = tuple(bibliography.values())
        index = build_index(bibliography_tuple)
        logger.info("Index built successfully")
    except Exception as e:
        error_msg = f"Failed to build index: {e.__class__.__name__}: {e}"
        logger.error(error_msg)
        return Err(message=error_msg, code=-1, error_type="IndexBuildError")

    # Step d: Process each staged item to find matches
    logger.info("Processing staged items...")
    try:
        staged_with_matches = stage_bibitems_batch(
            staged_items, index, top_n=top_n, min_score=min_score
        )
        logger.info(f"Processed {len(staged_with_matches)} items")

        # Log summary statistics
        total_matches = sum(len(item.top_matches) for item in staged_with_matches)
        avg_matches = total_matches / len(staged_with_matches) if staged_with_matches else 0
        logger.info(f"Found {total_matches} total matches (avg {avg_matches:.2f} per item)")

        if staged_with_matches:
            avg_time = sum(
                item.search_metadata["search_time_ms"] for item in staged_with_matches
            ) / len(staged_with_matches)
            logger.info(f"Average search time: {avg_time:.0f}ms per item")

    except Exception as e:
        error_msg = f"Failed to process staged items: {e.__class__.__name__}: {e}"
        logger.error(error_msg)
        return Err(message=error_msg, code=-1, error_type="ProcessingError")

    # Step e: Write report
    logger.info("Writing report...")
    write_result = write_report(output_path, staged_with_matches)
    if isinstance(write_result, Err):
        logger.error(f"Failed to write report: {write_result.message}")
        return write_result

    logger.info("Fuzzy matching procedure completed successfully")
    return Ok(None)
