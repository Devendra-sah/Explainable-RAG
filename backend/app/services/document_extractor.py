from pathlib import Path

from pypdf import PdfReader
from docx import Document


class DocumentExtractor:

    def extract(self, file_path: str):

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        extension = path.suffix.lower()

        if extension == ".pdf":
            return self._extract_pdf(path)

        elif extension == ".docx":
            return self._extract_docx(path)

        elif extension == ".txt":
            return self._extract_txt(path)

        else:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )


    # ==================================================
    # PDF
    # ==================================================

    def _extract_pdf(self, path: Path):

        reader = PdfReader(str(path))

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            text = page.extract_text() or ""

            pages.append({
                "page_number": page_number,
                "text": text
            })

        return {
            "file_type": "pdf",
            "page_count": len(pages),
            "pages": pages
        }


    # ==================================================
    # DOCX
    # ==================================================

    def _extract_docx(self, path: Path):

        document = Document(str(path))

        blocks = []

        current_section = None

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if not text:
                continue

            style_name = ""

            if paragraph.style:
                style_name = paragraph.style.name


            # ------------------------------------------
            # Detect headings
            # ------------------------------------------

            if style_name.startswith("Heading"):

                current_section = text

                blocks.append({
                    "type": "heading",
                    "text": text,
                    "style": style_name
                })

            else:

                blocks.append({
                    "type": "paragraph",
                    "text": text,
                    "style": style_name,
                    "section_title": current_section
                })


        return {
            "file_type": "docx",
            "blocks": blocks
        }


    # ==================================================
    # TXT
    # ==================================================

    def _extract_txt(self, path: Path):

        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        return {
            "file_type": "txt",
            "text": text
        }