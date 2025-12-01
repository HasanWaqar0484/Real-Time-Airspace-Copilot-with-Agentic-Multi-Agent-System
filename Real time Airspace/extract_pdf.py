import sys

def extract_text(pdf_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            print("Neither pypdf nor PyPDF2 is installed.")
            return None
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    text = extract_text(pdf_path)
    with open("instructions.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Text extracted to instructions.txt")
    if not text:
        sys.exit(1)
