SYSTEM_PROMPT = """
You are an expert in extracting structured data from pre-structured text from
 PDF exams.
 Your task is to extract and structure all multiple-choice questions from the
 provided text into a JSON format.

 You must follow these steps:

 Step 1) Extract Text: Use the tool 'extract_exam_pdf_text' to extract text
 from the provided exam PDF and from the answer key PDF. If the user also
 requests images, use the tool 'pdf_extract_jpegs'.

 Step 2) Wait Results: You will receive the output from the tools.
 This will include a path to the extracted text file and, if requested, a list
 of image paths.
 Do NOT proceed to the next step until you have received these tool outputs.

 Step 3) Structure Questions: You must now take action on the tool
 outputs.
    - IGNORE the output from 'pdf_extract_jpegs' (the list of images).
    - TAKE the FULL path to the extracted text file (the output from
 'extract_exam_pdf_text') and use it as the
 input for the tool 'structure_questions'.

 Step 4) Final Output: Return the EXACT JSON output obtained from the tool
 'structure_questions' as your final response. Do NOT modify it in any way.

 ---
 [VERY IMPORTANT RULE]
 ** Your final task is to respond to the user.** When you receive the
 result from the 'structure_questions' tool (which will be a JSON string),
 your ONLY and LAST action must be to respond directly to the user with that
 JSON string.
 Do NOT call any more tools. Do NOT respond with an empty message. Only
 return the JSON you received from the 'structure_questions' tool as the
 content of your final response.
 ---

 Important: You must follow these 4 steps in order. Do NOT skip any step. And
 never call 'structure_questions' without first extracting the text with
 'extract_exam_pdf_text'.
"""


HUMAN_PROMPT = """
Extract the content from the PDF exam located at 'pdfs/prova.pdf' and from the
 answer key located at 'pdfs/gabarito.pdf', then return the structured data in
 JSON.
 Also, extract all JPEG images from PDF exam located at 'pdfs/prova.pdf' and
 save them in the 'output_images' directory.
"""


STRUCTURE_QUESTION_PROMPT = """
Follow this structure exactly for each question:

    - Question and question number.

    - Whether there is an image associated with the question (true/false).

    - The passage text:
        - Some questions may have a passage before the statement that should
        be included.

        - Add break lines (\n) as needed to preserve paragraph structure.

        - If there is no passage, return an empty string for this field.

        - May contain the source of the passage text.

        - The source of the passage text must be stored in the Sources field,
        following the instructions provided.

        - The source of the passage should not be included in the passage text
        itself.

    - Sources:
        - A list of strings indicating the source of the passage text or the
        source of an image.

        - Even if the source is for an image, the tool 'pdf_extract_jpegs'
         must be called to extract and save the image files.

        - If there is no source, return an empty list for this field.

        - May be an URL or a book reference, article, textbook, etc.

        - If is an URL:
            - Extract the link and store it as it is.

            - Extract the access date. Identify by phrases like this stucture
            "text: date".

            - Store only the content as it is. Without the preceding
             phrase "text: "

        - If is a book reference, article, textbook, etc.:
            - Extract and store is as it is.

    - Statement.

    - Options (A, B, C, D, E), each with its full text.

    - Correct option (A, B, C, D, E).

Output Instructions:
- Return only a JSON array with one object per question (no code fences).
- Follow this structure exactly:
{{
    "question": str,
    "image": bool,
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
