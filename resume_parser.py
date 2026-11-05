
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_resume_text(pdf_source) -> str:
    """
    Extract text from a candidate's resume PDF.

    Accepts either a PDF file path or a file-like object.
    """

    # Step 1: Validate the PDF path, if provided
    if isinstance(pdf_source, (str, Path)):
        pdf_path = Path(pdf_source)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"Resume file not found: {pdf_path}"
            )

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError("Please provide a PDF file.")

    # Step 2: Reset file pointer when using an uploaded file
    if hasattr(pdf_source, "seek"):
        pdf_source.seek(0)

    # Step 3: Read the PDF
    try:
        reader = PdfReader(pdf_source)

        if reader.is_encrypted:
            raise ValueError(
                "Encrypted PDF files are not supported."
            )

        extracted_pages = []

        # Step 4: Extract text from every page
        for page in reader.pages:
            page_text = page.extract_text() or ""

            if page_text.strip():
                extracted_pages.append(page_text.strip())

        # Step 5: Combine text from all pages
        resume_text = "\n\n".join(extracted_pages)

        if not resume_text.strip():
            raise ValueError(
                "No readable text found in the resume PDF. "
                "The PDF may contain scanned images."
            )

        return resume_text

    except PdfReadError as error:
        raise ValueError(
            "Unable to read the resume PDF."
        ) from error


if __name__ == "__main__":

    pdf_path = input(
        "Enter the path to your resume PDF: "
    ).strip().strip('"')

    resume_text = extract_resume_text(pdf_path)

    print("\nRESUME TEXT EXTRACTED SUCCESSFULLY")
    print("=" * 50)

    print(f"Total characters: {len(resume_text)}")
    print("\nRESUME PREVIEW")
    print("=" * 50)
    print(resume_text[:1000])