# doc_writer.py
import odfdo as odf

STYLE_SOURCE = 'ICON_styles.odt'
OUT_PATH = "cards.odt"

def open_icon_doc():
    doc = open_doc()
    get_icon_styles(doc)
    return doc

def open_doc():
    return odf.Document('odt')

def save_doc(document: odf.Document, path: str) -> None:
    """Save a recipe result Document."""
    print("Saving:", path)
    document.save(path, pretty=True)

def get_icon_styles(document: odf.Document) -> None:
    # We want to change the styles of collection2.odt,
    # we know the odfdo_styles.odt document contains an interesting style,
    # So let's first fetch the style:
    style_document = odf.Document(STYLE_SOURCE)

    # We could change only some styles, but here we want a clean basis:
    document.delete_styles()

    # And now the actual style change:
    document.merge_styles_from(style_document)

if __name__ == "__main__":
    main()