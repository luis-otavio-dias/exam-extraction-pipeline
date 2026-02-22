from models.question import Question, QuestionOption
from processors.question_processor import QuestionProcessor


def test_attach_images_to_question() -> None:
    processor = QuestionProcessor()

    options: list[QuestionOption] = [
        QuestionOption(label="A", text="Option A"),
        QuestionOption(label="B", text="Option B"),
        QuestionOption(label="C", text="Option C"),
        QuestionOption(label="D", text="Option D"),
    ]

    structured_questions: list[Question] = [
        Question(
            question="question 01",
            statement="What is shown in the image?",
            options=options,
            correct_option="A",
            image=True,
        ),
        Question(
            question="question 02",
            statement="What is the capital of France?",
            options=options,
            correct_option="B",
            image=False,
        ),
        Question(
            question="question 03",
            statement="Identify the object in the picture.",
            options=options,
            correct_option="C",
            image=True,
        ),
    ]

    question_image_map = {
        "question 01": ["http://example.com/image1.jpg"],
        "question 03": ["http://example.com/image2.jpg"],
    }

    processor.attach_images_to_questions(
        structured_questions, question_image_map
    )

    assert structured_questions[0].images == ["http://example.com/image1.jpg"]
    assert (
        structured_questions[1].images is None
        or structured_questions[1].images == []
    )
    assert structured_questions[2].images == ["http://example.com/image2.jpg"]
