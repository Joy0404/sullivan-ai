# 기여 방법

이 저장소는 단일 통합 제품과 `main` 브랜치를 기준으로 합니다. 작은 변경은 `fix/<name>` 또는 `feat/<name>` 브랜치에서 작업한 뒤 `main`으로 Pull Request를 보냅니다.

## Pull Request 필수 항목

- 완성한 사용자 행동
- 정상 입력과 실제 결과
- 낮은 확신도·모델 실패·문제 정답 중 관련 예외 결과
- 원본 영상 또는 학습자료의 전송·저장 여부
- 실행한 자동 테스트
- 키보드와 음성 출력 확인 결과
- 실제 구현과 데모 데이터를 구분한 설명

## 안전 변경

`safe_to_speak`, 확신도 임계값, 문제 모드, 원본 미디어 처리, TTS 출력 경로를 변경할 때는 반드시 회귀 테스트를 추가합니다. 공급자별 코드는 `apps/api/app/adapters` 안에 두고 핵심 에이전트가 특정 SDK에 종속되지 않게 합니다.

## 커밋 예시

```text
feat(agent): detect unspoken formula changes
feat(web): add non-visual passage navigation
test(safety): hide low-confidence OCR content
docs(scope): mark live analyzer as adapter-required
```
