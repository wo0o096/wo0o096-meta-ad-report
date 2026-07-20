# SuperPlanet 주간 소재 성과보고서 — 생성 스펙

> 주간 리포트 자동화(매주 월요일)가 이 문서를 기준으로 데이터 집계·HTML 생성·Slack 발송을 수행한다.
> 이 문서와 루틴 지시문이 충돌하면 **이 문서가 우선**한다. (최종 수정: 2026-07-15)

## 1. 데이터 소스

| 채널 | 소스 | 비고 |
|---|---|---|
| Google | 스프레드시트 `구글 애즈 소재분석 raw 정제작업`의 `raw_{게임}` 시트 | 매주 월 5-6시 KST Google Ads Script가 갱신 |
| Meta | Singular (source=Facebook, 최근 14일~어제) | dimensions: app, os, campaign, adn_creative_name / metrics: cost, impressions, installs, Total Revenue LTV, Total ROI LTV |

- 기간: 어제까지의 최근 14일 (월~일 2주), 금액은 KRW.
- 앱 매핑·제외 게임은 루틴 지시문을 따른다. ROAS = Total Revenue LTV / Cost (Meta), 전환 가치 / 비용 (Google).
- **구매(결과) 컬럼은 어디에도 표시하지 않는다.**

## 2. 소재 필터링

### Google — 시각 소재만
- `앱 확장 소재 유형` 기준: `YouTube 동영상` → **영상**, `*이미지` (가로형/정방형/세로형 등) → **이미지**.
- `광고 제목`, `설명`, 빈 유형 등 텍스트 컴포넌트는 **제외** (텍스트에 비용이 많이 잡히지만 크리에이티브 성과가 아님).

### 소재명 정제 (Google만)
1. 앞 정렬 번호 제거: `3-1.`, `9-3.`, `8.` 등 (`^\d+(-\d+)?\.\s*`)
2. 끝 해상도/확장자 제거: `_1200x628.jpg`, `_1080x1080.png` 등 (`_\d+x\d+\.(jpg|jpeg|png|gif)$`, 확장자만 있는 경우 포함)
3. Creative Name 내 줄바꿈 → 공백
4. Creative Name이 비어 있으면 `앱 확장 소재`의 파일명 부분 사용

### Meta — 소재명 정제
- ` - 사본` 접미사(중복 포함) 제거 후 원본과 합산.

## 3. 합산 기준

- **정제된 소재명 단위로 캠페인 무관 합산.** Meta는 (소재명 × Singular OS) 단위 유지.
- 합산 항목: 지출, 노출, 설치, 매출(전환 가치/Revenue LTV).
- 합산 후 재계산: CPI = 지출/설치, ROAS = 매출/지출.

## 4. 지출 임계값 (합산 후)

| 채널 | 임계값 |
|---|---|
| Meta | 지출 > 300,000원 |
| Google | 지출 > 100,000원 |
| 신규/소액 게임 (`no_threshold_games`) | 임계값 없음, 지출 상위 5개만 표시 |

- `no_threshold_games`: 출시 4주 이내이거나 채널 지출이 200만원 미만인 게임 (예: 던전견문록, 사전예약 캠페인).
- 임계값 미달로 표시 소재가 3개 미만이면 해당 게임·채널도 no-threshold 방식(상위 5개)으로 폴백.

## 5. HTML 랭킹 테이블 기준

| 테이블 | 정렬 | 조건 | 개수 |
|---|---|---|---|
| Top 5 소재 (지출) | 지출 내림차순 | 지출 > 0 | 5 |
| Best ROAS 소재 | ROAS 내림차순 | ROAS ≥ 0.5 + 지출 ≥ 10,000원 + 노출 ≥ 50,000회 | 10 |
| Best CPI 소재 | CPI 오름차순 | 설치 > 0 + CPI > 0 + 노출 ≥ 50,000회 | 10 |
| Best CPR (사전예약 전용) | 전환당 비용 오름차순 | CPR > 0 + 지출 ≥ 10,000원 | 10 |

- 사전예약 캠페인: Cost, eCPI(또는 CPR), 유형만 표시 — ROAS 없음. Singular가 사전예약을 기존 앱으로 오매핑할 수 있으므로 근사치 표기.

### 표시 개수 규칙 (중요)
- **Top 5 (지출)**: 5개. 소재가 부족하면 있는 만큼만.
- **Best ROAS / Best CPI / Best CPR**: 각각 상위 10개. 조건을 충족하는 소재가 10개 미만이면 그 수만 표시하고, **0개면 섹션 자체를 숨긴다** (제목도 출력하지 않음).
- 사전예약 참고용(Meta 오매핑) 보조 블록도 상위 10개로 제한.
- Best ROAS/CPI의 노출 ≥ 50,000 조건 때문에 Google처럼 소재가 잘게 쪼개진 채널은 두 섹션이 비어 숨겨지는 것이 정상 동작이다 (Top 5만 남음).

## 6. 유형·플랫폼 판별

- **Meta**: 소재명에 `영상` → 영상, `이미지` → 이미지, `다이내믹` → 다이내믹, 그 외 → 캐러셀. 플랫폼은 Singular OS 차원 사용 (소재명 `_iOS_`/`_AOS_`와 충돌 시 OS 차원 우선).
- **Google**: `앱 확장 소재 유형`으로 판별 (YouTube 동영상=영상, *이미지=이미지). 플랫폼은 캠페인명 `_iOS_`/`_AOS_`.

## 7. Slack 발송 형식 (2단 스레드 구조)

### 메인 메시지 — 아래 항목만 포함
```
📊 SuperPlanet 광고 소재 성과보고서 | YYYY.MM.DD (요일) ~ YYYY.MM.DD (요일) | Wnn-Wnn

🎯 이번 주 하이라이트
• 🏆 최고 ROAS 소재: `소재명 (OS 유형)` — 게임명 채널 · ROAS n.nn (지출 nn만)
• 📈 채널 Best: 게임명 채널 ROAS n.nn (지출 n,nnn만 — 맥락 한 줄)
• ⚠️ 관심 필요: 게임명 — 채널별 ROAS와 지출, 점검 제안 한 줄

👉 전체 보고서 보기: <GitHub Pages URL>
🧵 게임별 상세는 이 메시지의 스레드를 확인해주세요.
```
- 하이라이트 선정 기준: 최고 ROAS는 지출 10만원 이상 소재 중 1위. 채널 Best는 지출 상위 채널 중 ROAS 최고. 관심 필요는 지출이 크고 ROAS가 낮은 게임/채널.
- **이번 주 총합, 게임별 한줄 요약 섹션은 넣지 않는다.**

### 스레드 댓글 — 게임별 상세 (게임당 1댓글)
```
:이모지: *게임명*

*Meta*
`1. 소재명 (OS 유형)`  nn만  ·  ROAS *n.nn*
... (Top 5)

*Google*
`1. 소재명`  nn만  ·  ROAS *n.nn*
... (Top 5)
```
- 게임 이모지: ⚔️ 소드마스터 스토리 · 😈 이블헌터타이쿤 · 🗡️ 갓슬레이어 · 🛡️ 언더다크 · 🐱 네코맨서 · 😇 갓갓갓 · 🔮 위키드 (신규 게임은 어울리는 이모지 선택)
- 사전예약은 `지출 · 전환 n건 (사전예약, ROAS 없음)` 형식.

## 8. 기준의 배경 (Why)

| 기준 | 이유 |
|---|---|
| Meta 30만 / Google 10만 임계값 | Google raw는 캠페인·소재별로 잘게 쪼개져 소재당 지출이 작음. 실효 소재만 표시 |
| 시각 소재만 (Google) | 텍스트 컴포넌트는 실제 크리에이티브 성과가 아님 |
| ROAS ≥ 0.5 + 노출 5만 | 저노출·저지출 소재의 우연한 고ROAS 오해 방지 |
| CPI 노출 5만 조건 | 소량 노출로 우연히 설치 잡힌 케이스 배제 |
| 소재명 합산 | 같은 소재를 여러 캠페인에서 운영해도 통합 성과 파악 |
| 번호/해상도 제거 | Google Ads UI 정렬번호·파일 규격 노이즈 제거 |
| Slack 2단 구조 | 채널 청결도 — 메인은 하이라이트만, 상세는 스레드 |

## 9. 발행 후 검증 (GitHub Pages 배포 확인)

Slack 발송 전, master에 푸시한 커밋의 GitHub Pages 배포가 실제로 완료되었는지 확인한다. HTML 파일이 저장소에 존재한다고 해서 `wo0o096.github.io/...` 링크가 즉시 살아있는 것은 아니다 — 배포 자체가 멈추는 경우가 있다.

> **2026-07-20 변경**: 저장소 Settings → Pages → Source를 "Deploy from a branch"에서 **"GitHub Actions"**로 전환했고, `.github/workflows/pages.yml` (`Deploy Pages (Actions-based, fallback for stuck legacy builder)`, workflow_id 316528962)이 배포를 전담한다. 기존 `pages-build-deployment`(workflow_id 259923820, 레거시 브랜치 빌더)는 더 이상 배포를 수행하지 않으며 참고용으로만 남는다. 아래 절차는 `pages.yml` 워크플로 기준으로 확인한다.

1. 리포트 커밋 푸시 직후, `actions_list` method=`list_workflow_runs`, resource_id=`316528962`(또는 파일명 `pages.yml`)로 최신 run을 조회하고 `head_sha`가 방금 커밋과 일치하는지 확인한다.
2. 짧게(대략 20~30초, 이 워크플로는 보통 15~20초 내 완료) 기다린 뒤 `actions_get` method=`get_workflow_run`으로 상태를 재확인한다.
   - `completed` + `conclusion: success` → 정상. Slack 발송 진행.
   - 계속 `queued`/`in_progress`이거나 `failure`인 경우 → 3번으로.
3. 복구 시도 (순서대로, 각 시도 후 재확인):
   - `failure`면 `actions_get` method=`get_workflow_run_logs_url`로 로그를 확인해 원인(권한/설정 문제 등)을 파악한다 — Actions 기반 배포는 실패 시 로그가 남으므로 레거시 빌더처럼 원인불명 정체가 발생하지 않는 것이 정상이다.
   - `queued`/`in_progress`가 비정상적으로 오래 지속되면 `actions_run_trigger` method=`cancel_workflow_run` → method=`rerun_workflow_run`, 또는 method=`run_workflow`(workflow_dispatch)로 재시도.
   - 그래도 안 풀리면 빈 커밋(`git commit --allow-empty`)으로 새 배포를 트리거.
4. 위 시도 후에도 몇 분 내 `success`로 전환되지 않으면: **Slack 발송을 보류하지 말고, 배포 상태를 명시한 채로 발송**하되 GitHub Pages 링크 대신/추가로 저장소 파일 링크(`github.com/.../blob/master/<filename>`)를 임시로 첨부하거나, "링크가 아직 반영되지 않을 수 있음" 경고를 메인 메시지에 덧붙인다. 이후 배포가 완료되면 같은 스레드에 정상 링크를 후속 댓글로 남긴다.
5. 이 저장소는 `github.io` 도메인이 샌드박스 프록시에서 차단되어 있어(WebFetch/curl 403) 링크를 직접 열어 검증할 수 없다 — Actions API 상태만으로 판단한다.
