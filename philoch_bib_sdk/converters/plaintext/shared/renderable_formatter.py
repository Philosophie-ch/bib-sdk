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
            value = getattr(text, bibstring_type)
            if not value:
                return ""
            return f"{value}"

        case BaseNamedRenderable(name, id):
            value = getattr(name, bibstring_type)
            if not value:
                return ""
            return f"{value}"

        case _:
            raise TypeError("Invalid type for renderable")
