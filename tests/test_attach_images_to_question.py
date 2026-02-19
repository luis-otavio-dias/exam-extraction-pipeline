from processors.question_processor import QuestionProcessor


def test_attach_images_to_question() -> None:
    processor = QuestionProcessor()

    structured_questions = [
        {"question": "What is shown in the image?", "image": True},
        {"question": "What is the capital of France?", "image": False},
        {"question": "Identify the object in the picture.", "image": True},
    ]

    question_image_map = {
        "What is shown in the image?": ["http://example.com/image1.jpg"],
        "Identify the object in the picture.": [
            "http://example.com/image2.jpg"
        ],
    }

    processor.attach_images_to_questions(
        structured_questions, question_image_map
    )

    assert structured_questions[0]["images"] == [
        "http://example.com/image1.jpg"
    ]
    assert "images" not in structured_questions[1]
    assert structured_questions[2]["images"] == [
        "http://example.com/image2.jpg"
    ]
