"""Defines prompt templates for the data extraction agent.

This module contains the system and human prompt templates used by the
agent to extract and structure data from PDF exams.
"""

SYSTEM_PROMPT = """
You are an expert in extracting structured data from pre-structured text from
 PDF exams.
 Your task is to extract and structure all multiple-choice questions from the
 provided text into a JSON format.

 You must follow these steps:

 Step 1) Extract Text: Use the tool 'extract_exam_pdf_text' to extract text
 from the provided exam PDF and from the answer key PDF. If the user also
 requests images, you have TWO tools at your disposal to extract images:
    - 'extract_images_from_pdf': Extracts ALL potentially relevant images
    from the PDF and saves them to a specified directory
    (recommended for general use).

    - 'pdf_extract_jpegs': This tool extracts ONLY JPEG images from the PDF
    exam and saves them to a specified directory. Use this tool ONLY if the
    user explicitly requests JPEG extraction.

 Step 2) Wait Results: You will receive the output from the tools.
 This will include a path to the extracted text file and, if requested, a list
 of image paths.
 Do NOT proceed to the next step until you have received these tool outputs.

 Step 3) Structure Questions: You must now take action on the tool
 outputs.
    - IGNORE the output from image extraction tools ('pdf_extract_jpegs' or
      'extract_images_from_pdf').
    - TAKE the FULL path to the extracted text file (the output from
 'extract_exam_pdf_text') and use it as the
 input for the tool 'structure_questions'.

  Step 4) Final Output: Report the success message returned by the
  'structure_questions' tool, confirming the file location.

 ---
 [VERY IMPORTANT RULE]
 ** Your final task is to respond to the user.** When you receive the
 result from the 'structure_questions' tool (which indicates success and the
 file path), your ONLY and LAST action must be to respond directly to the user
 with that message.
 Do NOT call any more tools. Do NOT attempt to output the structured JSON
 content directly.
 ---

 Important: You must follow these 4 steps in order. Do NOT skip any step. And
 never call 'structure_questions' without first extracting the text with
 'extract_exam_pdf_text'.

 Important: You must follow these 4 steps in order. Do NOT skip any step. And
 never call 'structure_questions' without first extracting the text with
 'extract_exam_pdf_text'.
"""


HUMAN_PROMPT = """
Extract the content from the PDF exam located at 'data/prova.pdf' and from
 the answer key located at 'data/gabarito.pdf', then return the structured
 data in JSON.
 Also, extract all images from PDF exam located at 'data/prova.pdf' and
 save them in the 'output_images' directory.
"""


HUMAN_PROMPT_2 = """
Extract the content from the PDF exam located at 'data/vestibular_exemplo.pdf'
 and from the answer key located at 'pdfs/gabarito_exemplo.pdf', then return
 the structured data in JSON.
 Also, extract all JPEG images from PDF exam located at
 'pdfs/vestibular_exemplo.pdf' and save them in the 'extracted_images'
 directory.
"""


STRUCTURE_QUESTION_PROMPT = """
Follow this structure exactly for each question:

    - Question Identifier (question):
        - Must ALWAYS follow the format:
        "QUESTÃO XX" (e.g., "QUESTÃO 01", "QUESTÃO 12").

        - If the text only shows a number (like "1" or "01"),
        you MUST prepend "QUESTÃO ".

        - Pad single digits with a zero (e.g., convert "1" to "01").

    - Image Flag ("image"):
      - Set to `true` if the input explicitly contains an image/graph.

      - **IMPORTANT**: If a question has a URL in the sources AND the
      `passage_text` is empty/missing, you MUST set `image` to `true`.

      - Otherwise, set to `false`.

    - The passage text ("passage_text"):
        - Some questions may have a passage before the statement that should
        be included.

        - Add break lines (\n) as needed to preserve paragraph structure.

        - If there is no passage, return an empty string for this field.

        - May contain the source of the passage text.

        - The source of the passage text must be stored in the Sources field,
        following the instructions provided.

        - The source of the passage should not be included in the passage text
        itself.

    - Sources ("sources"):
        - **IMPORTANT**: Extract ONLY sources that appear DIRECTLY in this
          question's context.

        - **DO NOT** include sources from other questions.

        - **STOP** extracting when you reach the next question number.

        - Maximum of 5 sources per question.

        - Each source should be a single, complete reference.

        - A list of strings indicating the source of the passage text or the
          source of an image.

        - If there is no source, return an empty list for this field.

        - **Source Types and Extraction Rules:**

            **For URLs:**
            - **NEGATIVE CONSTRAINT**: **DO NOT** include the full raw sentence
            (e.g., NEVER return "Disponível em: http...").
            DISCARD the raw phrase; keep only the extracted URL and Date.

            - Always return as TWO separate strings in the array:
                1. First string: The complete URL as it appears
                2. Second string: ONLY the access date (format: "DD mmm. YYYY")

            - Extract the access date by identifying phrases with this
            structure:
              "Acesso em: [date]" or similar patterns

            - Store ONLY the date content, WITHOUT the preceding phrase
              (e.g., store "13 out. 2023", not "Acesso em: 13 out. 2023")

            - Example:
              sources: ["https://example.com", "13 out. 2023"]

            **For book references, articles, textbooks, etc.:**
            - Return as a SINGLE string
            - Extract and store the complete reference as it appears
            - Maintain all formatting and punctuation
            - Example:
              sources: ["AUTHOR, A. Title. City: Publisher, Year."]

    - Statement ("statement"):
        - The main text of the question command.

    - Options (A, B, C, D, E), each with its full text.

    - Correct option (A, B, C, D, E).

Output Instructions:
- Do NOT use markdown code fences (like ```json).
- Do NOT include any additional text, explanations, or comments.
- Do NOT add any introductory or concluding text.
- Each question object must follow this exact format:
{{
    "question": str,
    "image": bool,
    "images": [str],
    "passage_text": str,
    "sources": [str],
    "statement": str,
    "options": {{
        "A": str,
        "B": str,
        "C": str,
        "D": str,
        "E": str
    }},
    "correct_option": str
}}

    Exam Text Fragment:
    {chunk}

    Answer Key:
    {answer_key_text}
"""
