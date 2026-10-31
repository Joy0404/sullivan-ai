# 무료 배포 상태 — 2026-11-01

- 공개 서버: https://sullivan-ai-qlc5.onrender.com
- Render: Free, Singapore, 유료 영구 디스크 없음.
- Neon: sullivan-ai / morning-violet-94530569, production 브랜치.
- 조직: org-empty-cake-14402972. Free 플랜과 AWS Singapore를 실제 API로 확인함.
- Neon CLI 인증, init, deploy 완료. Postgres만 사용하며 추가 서비스 변경은 없음.
- 운영 DB에 버전 관리된 스키마를 Direct 연결로 적용하고 Pooled 읽기를 확인함.
- DATABASE_URL / DATABASE_URL_UNPOOLED를 기존 Render 서비스에 비공개로 전달함.
- 별도 시험 브랜치에서 동시 요청 8개 중 3개 허용/5개 차단, 런타임 재초기화 후 기록 유지를 확인하고 시험 브랜치를 삭제함.

## 로컬 실행

Python 의존성 설치 후 `npm ci`, `npm run build`를 실행합니다.
`neon init` / `neon deploy`가 만든 `.env.local`은 Git과 배포 ZIP에서 제외됩니다.
`npm start`는 이 파일을 읽어 로컬 서버를 시작합니다.
배포 서버는 Render 환경변수를 사용하며 로컬 비밀값 파일을 올리지 않습니다.

## 남은 확인

Gemini API 키와 체험 코드의 실제 설정 및 정상 분석은 별도 확인이 필요합니다.
이번 검증은 Gemini 공급자 호출을 실행하지 않았습니다.
실제 공급자 파일 삭제와 휴대폰 실기기 검증도 아직 완료로 주장하지 않습니다.
