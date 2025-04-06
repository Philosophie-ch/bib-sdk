from philoch_bib_sdk.logic.models import BaseRenderable, BaseNamedRenderable, TBibString


def format_renderable(
    renderable: BaseRenderable | BaseNamedRenderable,
    bibstring_type: TBibString,
) -> str:
    """
    Format a base renderable object into a string representation.
    """

    match renderable:

        case BaseRenderable(text, id):
            if not text:
                return ""
            return f"{getattr(text, bibstring_type)}"

        case BaseNamedRenderable(name, id):
            if not name:
                return ""
            return f"{getattr(name, bibstring_type)}"

        case _:
            raise TypeError("Invalid type for renderable")
