from app.models import (
    AnalysisPackageInput,
    GlossaryItem,
    StudyGuide,
    TranscriptSegment,
    VisualObservation,
)


DEMO_PASSAGE = """인공지능은 많은 데이터를 바탕으로 일정한 규칙을 찾는다. 데이터의 품질이 낮으면 결과도 부정확해질 수 있다.

그러나 데이터가 많다고 해서 언제나 공정한 결과가 만들어지는 것은 아니다. 조사 대상이 한쪽 집단에 치우치면 인공지능도 그 편향을 학습할 수 있다. 따라서 데이터가 어떤 사람들을 대표하는지 함께 살펴야 한다.

결론적으로 인공지능을 책임 있게 사용하려면 정확도뿐 아니라 데이터의 대표성과 결과의 영향을 함께 확인해야 한다."""


STAR_PASSAGE = """별은 성운의 일부가 중력으로 수축하면서 원시별로 태어난다. 중심 온도가 충분히 높아져 수소 핵융합이 시작되면 주계열성이 된다.

별은 일생의 대부분을 주계열성으로 보내며, 이때 중심에서 수소가 헬륨으로 바뀐다. 중심의 수소가 줄어들면 중심부는 수축하고 바깥층은 팽창한다.

태양과 질량이 비슷한 별은 적색 거성, 행성상 성운을 거쳐 백색 왜성이 된다. 질량이 매우 큰 별은 초거성과 초신성을 거쳐 중성자별 또는 블랙홀이 된다.

따라서 별의 초기 질량은 별의 진화 속도와 마지막 단계, 그리고 우주에 퍼뜨리는 원소를 결정하는 핵심 조건이다."""


def build_demo_package() -> AnalysisPackageInput:
    """Return pre-authored accessibility data for the stellar-evolution sample."""

    return AnalysisPackageInput(
        transcript_segments=[
            TranscriptSegment(segment_id="star-speech-1", start_ms=0, end_ms=48_000, text="이번 강의에서는 별의 탄생부터 마지막 단계까지 별의 진화를 살펴봅니다.", confidence=0.96),
            TranscriptSegment(segment_id="star-speech-2", start_ms=150_000, end_ms=205_000, text="성운이 중력 수축하여 원시별이 되고 중심 온도가 높아집니다.", confidence=0.95),
            TranscriptSegment(segment_id="star-speech-3", start_ms=318_000, end_ms=380_000, text="중심에서 수소 핵융합이 시작되면 별은 주계열 단계에 들어갑니다.", confidence=0.96),
            TranscriptSegment(segment_id="star-speech-4", start_ms=610_000, end_ms=675_000, text="별의 진화 경로는 처음 만들어질 때의 질량에 따라 달라집니다.", confidence=0.95),
            TranscriptSegment(segment_id="star-speech-5", start_ms=884_000, end_ms=950_000, text="태양 정도 질량의 별은 적색 거성을 거쳐 마지막에 백색 왜성이 됩니다.", confidence=0.96),
            TranscriptSegment(segment_id="star-speech-6", start_ms=1_142_000, end_ms=1_214_000, text="질량이 큰 별은 초신성 폭발 뒤 중성자별이나 블랙홀로 남을 수 있습니다.", confidence=0.95),
            TranscriptSegment(segment_id="star-speech-7", start_ms=1_360_000, end_ms=1_430_000, text="별의 내부와 초신성 폭발 과정에서 만들어진 원소는 다시 우주로 퍼집니다.", confidence=0.95),
        ],
        visual_observations=[
            VisualObservation(observation_id="star-title", timestamp_ms=12_000, screen_type="slide", kind="concept", text="별의 진화: 탄생, 주계열 단계, 질량에 따른 최후", confidence=0.98, importance=0.64, annotation="화면 제목 아래에 오늘 다룰 세 단계가 순서대로 제시되어 있습니다."),
            VisualObservation(observation_id="star-birth-board", timestamp_ms=235_000, screen_type="board", kind="concept", text="칠판 판서: 성운(가스와 먼지) → 중력 수축 → 원시별 → 중심 수축 → 주계열성, 주계열성 중심 온도 약 10^7 K", confidence=0.96, importance=0.94, annotation="칠판에는 성운의 가스와 먼지가 중력 수축해 원시별을 이루고, 다시 중심 수축을 거쳐 주계열성이 되는 과정이 화살표로 연결되어 있습니다. 주계열성 아래에는 중심 온도 약 천만 켈빈이 적혀 있습니다."),
            VisualObservation(observation_id="star-main-sequence-balance", timestamp_ms=410_000, screen_type="slide", kind="condition", text="중력 수축과 내부 기체 압력이 평형을 이루면 주계열성이 안정된다.", confidence=0.95, importance=0.9, annotation="그림의 안쪽 화살표는 중력, 바깥쪽 화살표는 내부 기체 압력을 나타내며 두 힘이 평형을 이룹니다."),
            VisualObservation(observation_id="star-mass-fork", timestamp_ms=705_000, screen_type="graph", kind="graph", text="원시별에서 주계열성까지는 공통이고 이후 진화 경로가 질량에 따라 두 갈래로 나뉜다.", confidence=0.96, importance=0.96, annotation="진화 흐름도가 주계열성 이후 두 갈래로 나뉩니다. 위쪽은 질량이 큰 별, 아래쪽은 태양 정도 질량의 별입니다."),
            VisualObservation(observation_id="star-sun-path", timestamp_ms=835_000, screen_type="slide", kind="highlight", text="태양 정도 질량: 주계열성 → 적색 거성 → 행성상 성운 → 백색 왜성", confidence=0.97, importance=0.96),
            VisualObservation(observation_id="star-massive-path", timestamp_ms=1_055_000, screen_type="slide", kind="highlight", text="질량이 큰 별: 주계열성 → 초거성 → 초신성 → 중성자별 또는 블랙홀", confidence=0.97, importance=0.97),
            VisualObservation(observation_id="star-elements", timestamp_ms=1_285_000, screen_type="slide", kind="concept", text="초신성 폭발은 철보다 무거운 원소가 생성되어 우주 공간으로 퍼지는 과정과 연결된다.", confidence=0.94, importance=0.88, annotation="화면에는 초신성에서 무거운 원소가 생성되고 성간 물질로 퍼져 새 별의 재료가 되는 순환 화살표가 있습니다."),
            VisualObservation(observation_id="star-uncertain-number", timestamp_ms=1_478_000, screen_type="board", kind="number", text="경계 질량 수치 후보", confidence=0.48, importance=0.9),
        ],
        passage_text=STAR_PASSAGE,
        highlighted_texts=[
            "태양과 질량이 비슷한 별은 적색 거성, 행성상 성운을 거쳐 백색 왜성이 된다.",
        ],
        study_guide=StudyGuide(
            overview="별은 성운에서 태어나 주계열성으로 가장 긴 시간을 보낸다. 중심의 수소가 고갈된 뒤에는 초기 질량에 따라 진화 경로가 갈라진다. 태양 정도 질량의 별은 백색 왜성으로, 질량이 큰 별은 초신성 뒤 중성자별이나 블랙홀로 이어질 수 있다.",
            concept_map=[
                "성운 → 중력 수축 → 원시별",
                "원시별 → 중심 수소 핵융합 시작 → 주계열성",
                "태양 정도 질량 → 적색 거성 → 행성상 성운 → 백색 왜성",
                "큰 질량 → 초거성 → 초신성 → 중성자별 또는 블랙홀",
                "초신성에서 퍼진 원소 → 성간 물질 → 새로운 별과 행성의 재료",
            ],
            glossary=[
                GlossaryItem(term="주계열성", definition="중심에서 수소 핵융합을 하며 중력과 내부 압력이 평형을 이룬 안정된 별입니다."),
                GlossaryItem(term="적색 거성", definition="중심 수소가 줄어든 뒤 바깥층이 크게 팽창하고 표면 온도가 낮아진 별입니다."),
                GlossaryItem(term="초신성", definition="질량이 큰 별의 마지막 단계에서 일어나는 매우 큰 폭발로, 무거운 원소를 우주에 퍼뜨립니다."),
                GlossaryItem(term="백색 왜성", definition="태양 정도 질량의 별이 바깥층을 방출한 뒤 남기는 작고 밀도 높은 핵입니다."),
                GlossaryItem(term="원시별", definition="성운의 가스와 먼지가 중력으로 모여 만들어지는 별의 초기 단계입니다."),
            ],
            recall_questions=[
                "원시별이 주계열성이 되는 기준은 무엇일까요?",
                "별의 초기 질량이 진화 경로를 어떻게 바꾸나요?",
                "태양 정도 질량의 별과 질량이 큰 별의 마지막 단계를 비교해 보세요.",
                "초신성 폭발이 새로운 별과 행성의 재료와 연결되는 까닭은 무엇일까요?",
            ],
        ),
    )
