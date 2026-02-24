import hashlib
import re
import unicodedata


def _normalize_text(text: str) -> str:
    """
    Remove acentos, converte para lowercase,
    remove caracteres especiais e normaliza espaços.
    """
    if not text:
        return ""

    # Remove acentos
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")

    # Lowercase
    text = text.lower()

    # Substitui separadores por underscore
    text = re.sub(r"[--\-]", "_", text)

    # Remove caracteres não alfanuméricos exceto underscore
    text = re.sub(r"[^a-z0-9_ ]", "", text)

    # Espaços para underscore
    text = re.sub(r"\s+", "_", text)

    # Remove múltiplos underscores
    text = re.sub(r"_+", "_", text)

    return text.strip("_")


def _compact_variant(variant: str) -> str:
    """
    Compacta termos comuns para tornar o ID mais curto.
    Usa regex para padrões genéricos (caderno_X, tipo_X)
    e mapeamento fixo para termos conhecidos.
    """
    if not variant:
        return ""

    v = _normalize_text(variant)

    patterns = [
        (r"(\d+)o?_dia", r"d\1"),
        (r"(\d+)a?_fase", r"f\1"),
        (r"tipo_(\w+)", r"t\1"),
        (r"caderno_\d+(\w+)", r"\1"),
        (r"caderno_(\w+)", r"\1"),
    ]

    for pattern, replacement in patterns:
        v = re.sub(pattern, replacement, v)

    v = re.sub(r"_+", "_", v)
    return v.strip("_")


def extract_question_number(raw_label: str) -> int:
    """
    Extrai o número da questão a partir de um rótulo textual.

    Aceita formatos como:
        - "QUESTÃO 01"
        - "questão 42"
        - "Questão nº 7"
        - "Question 10"
        - "Q. 5"
        - "Q5"
        - "05"
        - "12"

    Args:
        raw_label: Rótulo bruto contendo o número da questão.

    Returns:
        Número da questão como inteiro.

    Raises:
        ValueError: Se nenhum número for encontrado no rótulo.
    """
    if not raw_label or not raw_label.strip():
        msg = f"raw_label is empty: '{raw_label}'"
        raise ValueError(msg)

    # Remove acentos para normalizar "questão" -> "questao"
    text = unicodedata.normalize("NFD", raw_label)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.strip().lower()

    # Padrões ordenados do mais específico ao mais genérico
    patterns = [
        # "questao 01", "questao nº 7", "questao n 3"
        r"quest[ao]+\s*(?:n[o.]?\s*)?(\d+)",
        # "question 10", "question no. 5"
        r"question\s*(?:no?\.?\s*)?(\d+)",
        # "q. 5", "q.5", "q 5"
        r"q\.?\s*(\d+)",
        # Apenas número(s): "05", "12"
        r"(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    msg = f"No question number found in: '{raw_label}'"
    raise ValueError(msg)


def build_question_id(
    exam_name_base: str,
    exam_name_sigle: str | None,
    exam_variant: str,
    exam_year: int,
    question_number: int,
) -> str:
    """
    Gera ID determinístico para questão.

    Formato:
    <exam>_<year>_<variant>_qXX_<hash>
    """

    try:
        question_number = int(question_number)
    except (ValueError, TypeError) as err:
        msg = "question_number must be an integer"
        raise ValueError(msg) from err

    # Prioriza sigla
    base = exam_name_sigle or exam_name_base

    base_norm = _normalize_text(base)

    variant_norm = _compact_variant(exam_variant)

    variant_norm = re.sub(rf"^{exam_year}_?", "", variant_norm)

    q_part = f"q{int(question_number):02d}"

    components = [base_norm, str(exam_year)]

    if variant_norm:
        components.append(variant_norm)

    components.append(q_part)

    readable_id = "_".join(components)

    raw = f"{base_norm}_{exam_year}_{variant_norm}_{question_number}"
    short_hash = hashlib.sha256(raw.encode()).hexdigest()[:8]

    return f"{readable_id}_{short_hash}"


if __name__ == "__main__":
    # Testes rápidos

    exams = {
        "vestibular_ufu": {
            "exam_name_sigle": "UFU",
            "exam_variant": "2025-2 - 1ª Fase - Tipo 1",
            "exam_year": 2025,
            "exam_style": "vestibular",
            "exam_type": "multiple_choice",
            "answer_key_location": "separate_document",
            "total_questions": 88,
        },
        "prova": {
            "exam_name_base": "Exame Nacional do Ensino Médio",
            "exam_name_sigle": "ENEM",
            "exam_variant": "2024 - 1º Dia - Caderno 1 - Azul",
            "exam_year": 2024,
            "exam_style": "enem_like",
            "exam_type": "mixed",
            "answer_key_location": "same_document",
            "total_questions": 90,
        },
    }

    print()
    qnum = extract_question_number("QUESTÃO 05")
    print(
        build_question_id(
            exam_name_base=exams["prova"]["exam_name_base"],
            exam_name_sigle=exams["prova"]["exam_name_sigle"],
            exam_variant=exams["prova"]["exam_variant"],
            exam_year=exams["prova"]["exam_year"],
            question_number=qnum,
        )
    )  # enem_2024_d1_azul_q05

    print()
    qnum = extract_question_number("Q. 3")
    print(
        build_question_id(
            exam_name_base="Vestibular da Universidade Federal de Uberlândia",
            exam_name_sigle=exams["vestibular_ufu"]["exam_name_sigle"],
            exam_variant=exams["vestibular_ufu"]["exam_variant"],
            exam_year=exams["vestibular_ufu"]["exam_year"],
            question_number=qnum,
        )
    )  # ufu_2025_f1_t1_q03
