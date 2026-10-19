from types import SimpleNamespace

from PIL import Image

from tenderproof.services import source_service


def test_scanned_pdf_ocr_processes_beyond_legacy_40_page_cap(tmp_path, monkeypatch):
    class Page:
        def render(self, scale):
            return SimpleNamespace(to_pil=lambda: Image.new("RGB", (100, 60), "white"))

    class Document:
        def __init__(self, _path):
            self.pages = [Page() for _ in range(144)]

        def __len__(self):
            return len(self.pages)

        def __getitem__(self, index):
            return self.pages[index]

    class Engine:
        def __call__(self, _image):
            return SimpleNamespace(txts=["recognized tender text"])

    import pypdfium2
    import rapidocr

    monkeypatch.setattr(pypdfium2, "PdfDocument", Document)
    monkeypatch.setattr(rapidocr, "RapidOCR", Engine)
    progress = []
    text, note = source_service._ocr_pdf(tmp_path / "scan.pdf", lambda current, total: progress.append((current, total)))

    assert text.count("[OCR page") == 144
    assert progress[0] == (1, 144)
    assert progress[-1] == (144, 144)
    assert "processed with local RapidOCR" in note
