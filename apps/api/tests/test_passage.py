from app.core.demo import DEMO_PASSAGE
from app.core.passage import navigate_passage, structure_passage


HIGHLIGHT = "조사 대상이 한쪽 집단에 치우치면 인공지능도 그 편향을 학습할 수 있다."


def test_structure_passage_preserves_paragraphs_flow_and_highlight() -> None:
    document = structure_passage(
        DEMO_PASSAGE,
        [HIGHLIGHT],
        [(HIGHLIGHT, 20_000)],
        title="데모 지문",
    )

    assert len(document.paragraphs) == 3
    assert document.sentence_count >= 5
    assert document.highlighted_count == 1
    assert document.paragraphs[1].flow_role == "반론·대조"
    assert document.paragraphs[2].flow_role == "필자의 결론"
    highlighted = next(
        sentence
        for paragraph in document.paragraphs
        for sentence in paragraph.sentences
        if sentence.highlighted
    )
    assert highlighted.timestamp_ms == 20_000


def test_navigation_supports_highlight_next_and_semantic_section() -> None:
    document = structure_passage(DEMO_PASSAGE, [HIGHLIGHT])

    highlighted = navigate_passage(document, "방금 밑줄 친 문장 읽어줘")
    assert HIGHLIGHT in highlighted.message

    next_sentence = navigate_passage(
        document,
        "다음 문장",
        highlighted.current_sentence_id,
    )
    assert next_sentence.current_sentence_id != highlighted.current_sentence_id

    conclusion = navigate_passage(document, "필자의 결론")
    assert "결론" in conclusion.message
    assert "책임 있게" in conclusion.message


def test_navigation_returns_safe_message_when_passage_missing() -> None:
    result = navigate_passage(None, "다음 문장")

    assert result.safe_to_speak is True
    assert result.sentence_ids == []
    assert "지문" in result.message

