# import re
# import uuid
from pathlib import Path

import fitz

MEDIA_DIR = Path("media_images")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"

images_saved = []

doc = fitz.open(pdf_path)
cont = 0

for page in doc.pages(1, 3):
    # page = doc.load_page(num_pagina)

    # 4. Pede a lista de imagens da página
    # full=True nos dá o xref (ID) de cada imagem
    lista_imagens = page.get_images(full=True)

    if not lista_imagens:
        continue

    # 5. Itera por cada imagem encontrada na página
    for index_img, img in enumerate(lista_imagens):
        # O 'xref' é o ID interno da imagem
        xref = img[0]

        try:
            # 6. Extrai os dados da imagem (bytes e extensão)
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # 7. Cria um nome de arquivo único e salva
            nome_arquivo = f"pagina_{cont + 1}_img_{index_img + 1}.{image_ext}"
            caminho_completo = MEDIA_DIR / nome_arquivo

            with caminho_completo.open("wb") as f:
                f.write(image_bytes)

            images_saved.append(caminho_completo)

        except Exception as e:
            print(
                f"Erro ao extrair imagem (xref={xref}) na página {cont + 1}: {e}"
            )

doc.close()
