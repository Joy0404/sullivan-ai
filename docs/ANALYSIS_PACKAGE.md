# 분석 패키지 계약

실제 영상 STT/OCR 모델과 Sullivan AI 코어 사이의 공급자 중립 계약이다. JSON Schema는 `packages/contracts/events.schema.json`에 있다.

## 최상위 필드

```json
{
  "transcript_segments": [],
  "visual_observations": [],
  "passage_text": null,
  "highlighted_texts": [],
  "study_guide": {
    "overview": "강의 핵심 요약",
    "concept_map": ["개념 A → 관계 → 개념 B"],
    "glossary": [{"term": "용어", "definition": "강의 맥락의 정의"}],
    "recall_questions": ["정답을 노출하지 않는 회상 질문"]
  }
}
```

모든 시간은 영상 시작 기준 밀리초다.

## 강사 전사

```json
{
  "segment_id": "speech-12",
  "start_ms": 7000,
  "end_ms": 11000,
  "text": "그러면 여기서 이렇게 됩니다.",
  "confidence": 0.95
}
```

## 화면 관측

```json
{
  "observation_id": "visual-15",
  "timestamp_ms": 9000,
  "screen_type": "board",
  "kind": "formula",
  "text": "v = v₀ + at",
  "confidence": 0.96,
  "importance": 0.96,
  "annotation": null,
  "metadata": {}
}
```

`screen_type`은 `board`, `passage`, `slide`, `graph`, `image` 중 하나다. `kind`는 `formula`, `number`, `condition`, `highlight`, `passage`, `graph`, `concept`, `decoration`, `answer` 중 하나다.

## 공급자 구현 규칙

1. 관측하지 않은 텍스트를 추측해서 넣지 않는다.
2. 모델의 원 확신도를 보존한다.
3. 시각적 강조는 원 문장과 가능한 한 동일한 문자열을 제공한다.
4. 수식은 화면의 기호를 보존한다.
5. 문제의 최종 정답은 `answer`로 분류한다.
6. 실패 시 빈 성공 결과 대신 명시적 오류를 반환한다.
7. 원본 프레임과 음성은 기본적으로 저장하지 않는다.
8. `study_guide`는 관측된 강의 내용만 사용하고 문제의 정답을 포함하지 않는다.

## 웹에서 사용

분석 JSON 파일 자체가 위 최상위 객체이거나 `{ "analysis": { ... } }` 형태여도 된다. [lecture_analysis_demo.json](../packages/test-fixtures/lecture_analysis_demo.json)을 복사해 실제 공급자의 결과로 교체할 수 있다.

## API

```text
POST /v1/lectures
POST /v1/lectures/{session_id}/assets
POST /v1/lectures/{session_id}/analysis
GET  /v1/lectures/{session_id}
POST /v1/lectures/{session_id}/navigate
POST /v1/lectures/{session_id}/end
```

개발 중 전체 입력·출력 모델은 `http://localhost:8000/docs`에서 확인한다.
