import re
from io import BytesIO
from pathlib import Path

import fitz
from fitz import Document
from PIL import Image


def _count_img_occurrences(doc: Document) -> dict[int, int]:
    """
    Count occurrences of each image in the PDF document.
    Args:
        doc (Document): The PDF document.
    Returns:
        dict[int, int]: A dictionary mapping image xref to its
        occurrence count.
    """
    image_counts = {}

    for page in doc.pages():
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]

            image_counts[xref] = image_counts.get(xref, 0) + 1
    return image_counts


def _img_passes_filters(  # noqa: PLR0913
    image: Image.Image,
    image_bytes: bytes,
    xref: int,
    image_counts: dict[int, int],
    min_width: int = 300,
    min_height: int = 300,
    min_size_bytes: int = 10240,
    max_repetitions: int = 1,
    min_unique_colors: int = 50,
) -> bool:
    """Check if an image passes the defined filters."""
    if image_counts[xref] > max_repetitions:
        return False

    if len(image_bytes) < min_size_bytes:
        return False

    width, height = image.size
    if width < min_width or height < min_height:
        return False

    aspcet_ratio = width / height
    max_aspect_ratio = 4.0
    min_aspect_ratio = 0.25
    if aspcet_ratio > max_aspect_ratio or aspcet_ratio < min_aspect_ratio:
        return False

    image_rgb = image.convert("RGB")
    colors = image_rgb.getcolors(maxcolors=10000)
    if colors and len(colors) < min_unique_colors:
        return False

    return not (image.mode == "P" and "transparency" in image.info)


def _save_image(
    image_bytes: bytes,
    output_path: Path,
    img_name: str,
) -> None:
    """Save image in the specified output path."""
    out_path = output_path / img_name
    with out_path.open("wb") as f:
        f.write(image_bytes)


def map_images_to_questions(  # noqa: PLR0912
    pdf_path: Path, output_dir: Path
) -> dict[str, list[str]]:
    """
    Extrai imagens e as mapeia para as questões baseando-se na posição Y
    na página.
    Retorna: {'QUESTÃO 01': ['caminho/img1.png'], 'QUESTÃO 02': []}
    """
    doc = fitz.open(pdf_path)
    question_map = {}

    re_header = re.compile(r"(QUESTÃO\s+\d+)", re.IGNORECASE)
    output_dir.mkdir(parents=True, exist_ok=True)
    image_counts = _count_img_occurrences(doc)

    for page in doc.pages():
        text_blocks = page.get_text("dict")["blocks"]
        questions = []

        for block in text_blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        match = re_header.search(span["text"])
                        if match:
                            digit_mach = re.search(r"\d+", match.group(1))
                            if digit_mach:
                                q_num = int(digit_mach.group())
                                q_name = f"QUESTÃO {q_num:02d}"
                                questions.append((q_name, block["bbox"][1]))
                                if q_name not in question_map:
                                    question_map[q_name] = []

        questions.sort(key=lambda x: x[1])

        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            img_rects = page.get_image_rects(xref)

            if not img_rects:
                continue

            img_y = img_rects[0].y0

            current_question = None

            for i, (q_name, q_y) in enumerate(questions):
                if i + 1 < len(questions):
                    next_q_y = questions[i + 1][1]
                else:
                    next_q_y = float("inf")

                if q_y <= img_y < next_q_y:
                    current_question = q_name
                    break

            if not current_question:
                continue

            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            try:
                image = Image.open(BytesIO(image_bytes))

                if _img_passes_filters(image, image_bytes, xref, image_counts):
                    img_filename = (
                        f"{current_question}_img{xref}.{base_image['ext']}"
                    )
                    _save_image(
                        image_bytes,
                        output_dir,
                        img_filename,
                    )

                    image_path = img_filename
                    if image_path not in question_map[current_question]:
                        question_map[current_question].append(image_path)

            except Exception as e:
                print(f"Error processing xref {xref}: {e}")

    doc.close()
    return question_map


if __name__ == "__main__":
    import time

    start = time.perf_counter()
    pdf_file = Path().parent / "data" / "prova.pdf"
    output_directory = Path("extracted_images")

    question_image_map = map_images_to_questions(pdf_file, output_directory)

    for question, images in question_image_map.items():
        print(f"{question}: {images}")

    end = time.perf_counter()
    print(f"Image extraction completed in {end - start:.2f} seconds.")
