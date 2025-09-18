from typing import Literal, Tuple, get_args

TBibTeXEntryType = Literal[
    "article",
    "book",
    "incollection",
    "inproceedings",
    "mastersthesis",
    "misc",
    "phdthesis",
    "proceedings",
    "techreport",
    "unpublished",
    "UNKNOWN",
]

TBasicPubState = Literal[
    "",
    "unpub",
    "forthcoming",
]

TPubState = Literal[
    "",
    "unpub",
    "forthcoming",
    "inwork",
    "submitted",
    "published",
]

TLanguageID = Literal[
    "",
    "catalan",
    "czech",
    "danish",
    "dutch",
    "english",
    "french",
    "greek",
    "italian",
    "latin",
    "lithuanian",
    "ngerman",
    "polish",
    "portuguese",
    "romanian",
    "russian",
    "slovak",
    "spanish",
    "swedish",
    "unknown",
]

TEpoch = Literal[
    "",
    "ancient-philosophy",
    "ancient-scientists",
    "austrian-philosophy",
    "british-idealism",
    "classics",
    "contemporaries",
    "contemporary-scientists",
    "continental-philosophy",
    "critical-theory",
    "cynics",
    "enlightenment",
    "existentialism",
    "exotic-philosophy",
    "german-idealism",
    "german-rationalism",
    "gestalt-psychology",
    "hermeneutics",
    "islamic-philosophy",
    "mathematicians",
    "medieval-philosophy",
    "modern-philosophy",
    "modern-scientists",
    "neokantianism",
    "neo-kantianism",
    "neoplatonism",
    "new-realism",
    "ordinary-language-philosophy",
    "phenomenology",
    "polish-logic",
    "pragmatism",
    "presocratics",
    "renaissance",
    "stoics",
    "theologians",
    "vienna-circle",
]

# Literal value constants for runtime validation
BIBTEX_ENTRY_TYPE_VALUES: Tuple[TBibTeXEntryType, ...] = get_args(TBibTeXEntryType)
PUB_STATE_VALUES: Tuple[TPubState, ...] = get_args(TPubState)
EPOCH_VALUES: Tuple[TEpoch, ...] = get_args(TEpoch)
LANGUAGE_ID_VALUES: Tuple[TLanguageID, ...] = get_args(TLanguageID)
