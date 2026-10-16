from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(file_bytes: bytes) -> list[dict]:
    reader = PdfReader(BytesIO(file_bytes))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append(
            {
                "page_number": page_number,
                "text": text,
            }
        )

    return pages