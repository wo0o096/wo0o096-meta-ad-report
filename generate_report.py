#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_report.py — SuperPlanet 주간 광고 소재 성과보고서 HTML 생성기

Reverse-engineered from SuperPlanet_Meta_Google_성과보고서_260720-260802.html
(the reference/"golden" report). Reproduces the exact CSS, password gate,
two-level tab structure, table markup and Chart.js wiring of that file, but
driven entirely by a JSON/dict data blob instead of hardcoded values.

This module is PURE TEMPLATING. It does not compute ROAS/CPI, does not
apply the REPORT_SPEC.md spend thresholds, and does not decide which
creatives qualify for a ranking table — all of that business logic must
already have happened upstream when the caller assembles the data dict.
The one exception is purely *presentational* derivation that the original
file itself does at render time (not at data-collection time):
  - rank badge class (badge-1/2/3/n) from a list's position
  - ROAS color class (roas-high/mid/low) from a numeric ROAS value
  - type/platform tag class (tag-vid/tag-img/... , tag-ios/tag-aos/...)
    from a type/platform label string
  - "만"/"억" compaction of KRW amounts (fmt_krw), mirroring the file's
    client-side fmtKRW() used for chart tooltips
Sections with zero rows are omitted entirely (no heading, no table) per
REPORT_SPEC.md §5.

============================================================================
JSON / DICT SCHEMA
============================================================================
Top-level keys:
{
  "period": {
    "start": "2026-07-20",       # ISO date, KST, Monday of the 2-week window
    "end":   "2026-08-02",       # ISO date, KST, Sunday of the 2-week window
    "generated_at": "2026-08-03 09:30"   # optional; str, "Generated ..." footer line.
                                          # Defaults to now (KST) if omitted.
  },
  "sub_title": "소재별 성과 분석 | 내부 공유용",   # optional, defaults to this exact string
  "games": [ <Game>, ... ]        # order = tab order = game_0, game_1, ...
}

<Game> = {
  "name": "소드마스터 스토리",     # required, display name used as tab label
  "color": "#1a73e8",             # required, hex color for --g-color (active tab bg/border)
  "emoji": "⚔️",                  # optional. NOT rendered in the tab label in the
                                   # reference file (tabs show plain text only) —
                                   # kept here only as metadata for callers who also
                                   # build the companion Slack message (REPORT_SPEC.md §7),
                                   # where the emoji IS used. Prefix it into "name"
                                   # yourself if you ever want it to show in the tab.
  "channels": {
      "meta":   <Channel>,        # required key, may be status="empty"
      "google": <Channel>         # required key, may be status="empty"
  }
}

<Channel> one of three shapes, selected by "status":

1) status = "normal"  (has real spend/ROAS data this period)
{
  "status": "normal",
  "metrics": {
      "spend": 13071104,                 # int KRW, required
      "installs": 1662,                  # int, required
      "avg_cpi": 7865,                   # int KRW, required
      "weighted_roas": 0.46,             # float, required (colored via roas-* thresholds)
      "impressions": 740000,             # int, required
      "active_creatives": 58,            # int, required — creatives shown in "운영 소재"
      "total_creatives": 58              # int, required — shown as "전체 N개" subtitle
  },
  "type_breakdown": [                    # → "🎨 소재 유형별 성과" mini-table + doughnut chart
      {"label": "영상", "count": 27, "spend": 10403920, "installs": 1458},
      {"label": "이미지", "count": 31, "spend": 2667184, "installs": 204}
      # caller should pre-sort by spend desc (matches reference file); order here
      # is used verbatim for both the mini-table rows and the doughnut chart
      # legend/color assignment (positional, not label-based).
  ],
  "platform_breakdown": [                # → "📱 플랫폼별 성과" mini-table + doughnut chart
      {"label": "iOS", "count": 34, "spend": 7117244, "installs": 580},
      {"label": "AOS", "count": 24, "spend": 5953860, "installs": 1082}
  ],
  "chart_top10": [                       # → left bar chart "Top 10 소재 (지출)"
      {"name": "모든언어_iOS_영상_출렁_세로_260609", "spend": 3335903},
      ...                                 # up to 10 items, spend desc
  ],
  "top5": [ <Creative>, ... ],           # → "💰 Top 5 소재 (지출 기준)"; up to 5 rows.
                                          # Empty list => section hidden entirely.
  "best_roas": [ <Creative>, ... ],      # → "🏆 Best ROAS 소재 ..."; up to 10 rows.
                                          # Empty/omitted list => section hidden
                                          # (this is also how the no_threshold_games
                                          # top-5-only fallback mode is represented:
                                          # just pass [] / omit the key).
  "best_cpi": [ <Creative>, ... ],       # → "⚡ Best CPI 효율 소재 ..."; up to 10 rows.
                                          # Empty/omitted => section hidden.
  "budget_comment": "기간 지출 1,307만원(...)"   # required for normal channels;
                                          # free text -> <textarea> default value
}

<Creative> = {
  "name": "모든언어_iOS_영상_출렁_세로_260609",  # required, used as both cell text and title=
  "type": "영상",                 # required. One of 영상/이미지/다이내믹/캐러셀, or any
                                   # other string (maps to tag-other per REPORT_SPEC §6
                                   # "그 외 → 캐러셀" is a data-classification rule, not
                                   # this template's concern — pass whatever label you want,
                                   # unrecognized labels get tag-other. See TAG_TYPE_CLASS.)
  "platform": "iOS",              # required. "iOS" -> tag-ios, "AOS" -> tag-aos, else tag-unk
  "spend": 3335903,               # int KRW, required
  "installs": 309,                # int, required for top5/best_roas/best_cpi
  "cpi": 10796,                   # int KRW, required for top5/best_cpi (plain, uncompacted)
  "roas": 0.42,                   # float, required for top5/best_roas (colored)
  "impressions": 212122           # int, required for top5/best_cpi (and shown in top5)
}
  # Only the fields needed by the specific table are read; extras are ignored.
  # For best_roas rows, "cpi"/"impressions" are not rendered (table has no such
  # columns) — only rank/name/type/platform/roas/spend/installs.
  # For best_cpi rows, "roas" is not rendered — only rank/name/type/platform/
  # cpi/spend/installs/impressions.

2) status = "prereg"  (pre-registration / conversion-only campaign, no ROAS)
{
  "status": "prereg",
  "spend": 42353746,              # int KRW, required — "사전예약 지출" metric
  "creative_count": 33,           # int, required — "소재수" metric
  "remap_caveat": true,           # bool, optional (default True). Controls whether the
                                   # longer Singular-remapping caveat sentence is appended
                                   # to the no-data note (see PREREG_NOTE_* below).
  "top": [                        # → "📝 사전예약 소재 (참고용 — Cost·eCPI만, ROAS 없음)"
      {"name": "...", "type": "영상", "platform": "iOS", "spend": 6370000,
       "ecpi": None}              # ecpi: int KRW or None/omitted -> renders "-"
      ...                          # up to 10 rows (REPORT_SPEC §5 "보조 블록도 상위 10개")
  ]
}

3) status = "empty"  (channel had zero spend/executions this period)
{
  "status": "empty"
}
  # Renders a single <p class="no-data">이 채널은 이번 기간 집행 내역이 없습니다.</p>
  # and nothing else (no metrics, no charts, no tables, no budget section).

============================================================================
USAGE
============================================================================
    from generate_report import generate_html
    html = generate_html(data_dict)
    open("out.html", "w", encoding="utf-8").write(html)

Or from the CLI:
    python3 generate_report.py data.json out.html
"""

from __future__ import annotations

import html as _html
import json
import re
import sys
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Constants copied verbatim from the reference report (do not change).
# ---------------------------------------------------------------------------

CHARTJS_CDN_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
PW_HASH = "50988484283c4e3845212a75b4614d6bef2381d69eada31465b5a020f9ceb723"

KST = timezone(timedelta(hours=9))

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]

TYPE_TAG_CLASS = {
    "영상": "tag-vid",
    "이미지": "tag-img",
    "다이내믹": "tag-dyn",
    "캐러셀": "tag-carousel",
}
DEFAULT_TYPE_TAG_CLASS = "tag-other"

PLATFORM_TAG_CLASS = {
    "iOS": "tag-ios",
    "AOS": "tag-aos",
}
DEFAULT_PLATFORM_TAG_CLASS = "tag-unk"

TYPE_CHART_COLORS = ['#1565c0', '#c62828', '#f57f17', '#616161', '#4527a0']
PLAT_CHART_COLORS = ['#2e7d32', '#e65100', '#616161', '#1565c0']
BAR_CHART_COLOR = 'rgba(66,133,244,0.75)'

DEFAULT_SUB_TITLE = "소재별 성과 분석 | 내부 공유용"

PREREG_NOTE_SHORT = "이 채널은 현재 사전예약/전환 최적화 캠페인만 운영 중이라 ROAS·CPI를 산출할 수 없습니다."
PREREG_NOTE_CAVEAT = " Singular가 사전예약 캠페인을 기존 출시 앱으로 오매핑할 수 있어 수치는 근사치입니다."
EMPTY_CHANNEL_NOTE = "이 채널은 이번 기간 집행 내역이 없습니다."

# ---------------------------------------------------------------------------
# The <style> block, copied byte-for-byte from the reference report.
# Do not hand-edit piecemeal; if the design changes, re-extract the whole
# block from a fresh reference file and paste it in whole.
# ---------------------------------------------------------------------------

STYLE_BLOCK = """

:root { --p:#1a73e8; --pl:#e8f0fe; --s:#34a853; --w:#fbbc04; --d:#ea4335; --bg:#f8f9fa; --c:#fff; --t:#202124; --ts:#5f6368; --b:#dadce0; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',-apple-system,'Noto Sans KR',sans-serif; background:var(--bg); color:var(--t); line-height:1.6; }
.hdr { background:linear-gradient(135deg,#1a73e8,#4285f4,#669df6); color:#fff; padding:40px 0 32px; text-align:center; }
.hdr h1 { font-size:32px; font-weight:800; margin-bottom:8px; letter-spacing:-0.5px; }
.hdr .sub { font-size:15px; opacity:.9; }
.hdr .per { display:inline-block; background:rgba(255,255,255,.22); padding:6px 18px; border-radius:18px; margin-top:12px; font-size:13px; font-weight:500; }
.ctn { max-width:1200px; margin:0 auto; padding:16px; }
/* ─── Level 1: 게임 탭 ─── */
.g-tabs { display:flex; gap:6px; flex-wrap:wrap; margin-top:18px; padding:8px; background:var(--c); border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,.08); }
.g-tab { flex:1; min-width:140px; padding:14px 16px; border:2px solid transparent; cursor:pointer; font-size:16px; font-weight:700; color:#455a64; background:#f5f5f5; border-radius:10px; transition:all .2s; text-align:center; letter-spacing:-0.3px; }
.g-tab:hover { background:#eceff1; transform:translateY(-1px); }
.g-tab.active { background:var(--g-color, #546e7a); color:#fff; border-color:var(--g-color, #546e7a); box-shadow:0 2px 8px rgba(0,0,0,.15); }

/* ─── 게임 섹션 (선택된 게임의 콘텐츠 컨테이너) ─── */
.game-section { display:none; }
.game-section.active { display:block; }

/* ─── Level 2: 채널 서브탭 (Meta / Google) ─── */
.ch-tabs { display:flex; gap:4px; margin-top:14px; padding:0; background:transparent; }
.ch-tab { flex:0 0 auto; min-width:130px; padding:10px 22px; border:none; cursor:pointer; font-size:14px; font-weight:700; border-radius:10px 10px 0 0; transition:all .2s; }
.ch-tab.tab-meta { background:#e3f2fd; color:#1565c0; }
.ch-tab.tab-google { background:#fff8e1; color:#a07700; }
.ch-tab.tab-meta:hover { background:#bbdefb; }
.ch-tab.tab-google:hover { background:#ffecb3; }
.ch-tab.tab-meta.active { background:#1976d2; color:#fff; }
.ch-tab.tab-google.active { background:#f9a825; color:#fff; }

/* 기존 .tabs/.tab-btn은 레거시 호환용 (사용 안 함) */
.tabs { display:none; }
.tab-pane { display:none; background:var(--c); border-radius:0 0 10px 10px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.08); }
.tab-pane.active { display:block; }
.metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:20px; }
.mc { background:var(--bg); border-radius:8px; padding:14px; text-align:center; border-left:3px solid var(--p); }
.mc .ml { font-size:11px; color:var(--ts); margin-bottom:2px; }
.mc .mv { font-size:20px; font-weight:700; color:var(--t); }
.mc .ms { font-size:10px; color:var(--ts); }
.charts-row { display:grid; grid-template-columns:1.5fr 1fr 1fr; gap:14px; margin-bottom:20px; }
.chart-box { background:var(--bg); border-radius:8px; padding:12px; position:relative; min-height:280px; }
.chart-box canvas { width:100% !important; height:100% !important; }
@media(max-width:900px) { .charts-row { grid-template-columns:1fr; } }
.analysis-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:20px; }
.analysis-card { background:var(--bg); border-radius:8px; padding:14px; }
.analysis-card h4 { font-size:13px; color:var(--ts); margin-bottom:8px; padding-bottom:4px; border-bottom:1px solid var(--b); }
.mini-table { width:100%; border-collapse:collapse; font-size:12px; }
.mini-table th, .mini-table td { padding:5px 6px; text-align:right; border-bottom:1px solid var(--b); }
.mini-table th { font-weight:600; color:var(--ts); font-size:11px; }
.mini-table td:first-child, .mini-table th:first-child { text-align:left; }
@media(max-width:768px) { .analysis-grid { grid-template-columns:1fr; } }
.sec-title { font-size:15px; font-weight:700; color:var(--t); margin:20px 0 10px; padding-bottom:6px; border-bottom:2px solid var(--pl); }
.ct-wrap { overflow-x:auto; margin-bottom:20px; }
table.ct { width:100%; border-collapse:collapse; font-size:12px; }
table.ct th { background:var(--p); color:#fff; padding:8px 6px; text-align:left; position:sticky; top:0; font-size:11px; white-space:nowrap; }
table.ct td { padding:7px 6px; border-bottom:1px solid var(--b); }
table.ct tr:hover { background:var(--pl); }
table.ct .num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
table.ct .ad-name { font-size:11px; max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
table.ct .rank { text-align:center; font-weight:700; color:var(--p); width:30px; }
.tag { display:inline-block; padding:1px 7px; border-radius:8px; font-size:10px; font-weight:600; }
.tag-img { background:#e3f2fd; color:#1565c0; }
.tag-vid { background:#fce4ec; color:#c62828; }
.tag-dyn { background:#fff8e1; color:#f57f17; }
.tag-carousel { background:#fff3e0; color:#e65100; }
.tag-other { background:#f5f5f5; color:#616161; }
.tag-ios { background:#e8f5e9; color:#2e7d32; }
.tag-aos { background:#fff3e0; color:#e65100; }
.tag-unk { background:#f5f5f5; color:#616161; }
.roas-high { color:var(--s); font-weight:700; }
.roas-mid { color:#e8a800; font-weight:600; }
.roas-low { color:var(--d); }
.badge-top { display:inline-block; width:22px; height:22px; line-height:22px; text-align:center; border-radius:50%; font-size:10px; font-weight:700; color:#fff; }
.badge-1 { background:linear-gradient(135deg,#ffd700,#ffb300); }
.badge-2 { background:linear-gradient(135deg,#b0bec5,#78909c); }
.badge-3 { background:linear-gradient(135deg,#a1887f,#795548); }
.badge-n { background:#e0e0e0; color:var(--ts); }
.ft { text-align:center; padding:20px; color:var(--ts); font-size:11px; margin-top:16px; }
.no-data { text-align:center; color:var(--ts); font-style:italic; padding:20px; font-size:13px; }
.budget-section { background:var(--bg); border-radius:8px; padding:16px; margin-bottom:20px; }
.budget-textarea { width:100%; min-height:140px; padding:12px 14px; border:1px solid var(--b); border-left:3px solid var(--p); border-radius:4px; background:var(--c); color:var(--t); font-family:inherit; font-size:13px; line-height:1.7; resize:vertical; outline:none; box-sizing:border-box; }
.budget-textarea:focus { border-color:var(--p); box-shadow:0 0 0 2px var(--pl); }
.budget-textarea::placeholder { color:var(--ts); font-style:italic; }
.budget-hint { font-size:11px; color:var(--ts); margin-top:6px; text-align:right; }

"""

# ---------------------------------------------------------------------------
# Small formatting / classification helpers (presentational logic only).
# ---------------------------------------------------------------------------


def esc(s) -> str:
    """HTML-escape a value (also handles non-str via str())."""
    return _html.escape(str(s), quote=True)


def fmt_krw(v: float) -> str:
    """Mirror the reference file's client-side fmtKRW() used for chart
    tooltips, also used here to render static 만/억-compacted spend figures
    (metric cards, table 지출 columns, chart data labels)."""
    v = float(v)
    if v >= 100_000_000:
        return f"{v / 100_000_000:.1f}억"
    if v >= 10_000:
        return f"{round(v / 10_000):,}만"
    return f"{round(v):,}"


def fmt_int(v) -> str:
    """Plain thousands-separated integer (used for CPI, impressions,
    installs table columns — these are never 만/억-compacted in the
    reference file)."""
    return f"{round(float(v)):,}"


def fmt_roas(v: float) -> str:
    return f"{float(v):.2f}"


def roas_class(v: float) -> str:
    v = float(v)
    if v < 0.5:
        return "roas-low"
    if v < 1.0:
        return "roas-mid"
    return "roas-high"


def type_tag_class(label: str) -> str:
    return TYPE_TAG_CLASS.get(label, DEFAULT_TYPE_TAG_CLASS)


def platform_tag_class(label: str) -> str:
    return PLATFORM_TAG_CLASS.get(label, DEFAULT_PLATFORM_TAG_CLASS)


def badge_class(rank_1based: int) -> str:
    return f"badge-{rank_1based}" if rank_1based <= 3 else "badge-n"


def tag_span(label: str, cls: str) -> str:
    return f'<span class="tag {cls}">{esc(label)}</span>'


def type_tag(label: str) -> str:
    return tag_span(label, type_tag_class(label))


def platform_tag(label: str) -> str:
    return tag_span(label, platform_tag_class(label))


def rank_cell(rank_1based: int) -> str:
    return (f'<td class="rank"><span class="badge-top {badge_class(rank_1based)}">'
            f'{rank_1based}</span></td>')


def weekday_ko(d: datetime) -> str:
    return WEEKDAY_KO[d.weekday()]


def fmt_period_date(d: datetime) -> str:
    return f"{d.year}.{d.month:02d}.{d.day:02d} ({weekday_ko(d)})"


def iso_week(d: datetime) -> int:
    return d.isocalendar()[1]


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def render_metrics_normal(m: dict) -> str:
    cards = []
    cards.append(
        '<div class="mc"><div class="ml">총 지출</div>'
        f'<div class="mv">{fmt_krw(m["spend"])}</div>'
        f'<div class="ms">{fmt_int(m["spend"])}원</div></div>'
    )
    cards.append(
        '<div class="mc"><div class="ml">총 설치</div>'
        f'<div class="mv">{fmt_int(m["installs"])}</div></div>'
    )
    cards.append(
        '<div class="mc"><div class="ml">평균 CPI</div>'
        f'<div class="mv">{fmt_int(m["avg_cpi"])}</div></div>'
    )
    rc = roas_class(m["weighted_roas"])
    cards.append(
        '<div class="mc"><div class="ml">가중 ROAS</div>'
        f'<div class="mv {rc}">{fmt_roas(m["weighted_roas"])}</div></div>'
    )
    cards.append(
        '<div class="mc"><div class="ml">노출</div>'
        f'<div class="mv">{fmt_krw(m["impressions"])}</div></div>'
    )
    cards.append(
        '<div class="mc"><div class="ml">운영 소재</div>'
        f'<div class="mv">{fmt_int(m["active_creatives"])}개</div>'
        f'<div class="ms">전체 {fmt_int(m["total_creatives"])}개</div></div>'
    )
    return '<div class="metrics">' + "".join(cards) + "</div>"


def render_charts_row(pane_idx: int) -> str:
    return (
        '<div class="charts-row">'
        f'<div class="chart-box"><canvas id="bar_{pane_idx}"></canvas></div>'
        f'<div class="chart-box"><canvas id="type_{pane_idx}"></canvas></div>'
        f'<div class="chart-box"><canvas id="plat_{pane_idx}"></canvas></div>'
        '</div>'
    )


def render_mini_table(rows: list) -> str:
    trs = ["<tr><th>유형</th><th>소재수</th><th>지출</th><th>설치</th></tr>"]
    for r in rows:
        trs.append(
            f'<tr><td>{esc(r["label"])}</td>'
            f'<td class="num">{fmt_int(r["count"])}</td>'
            f'<td class="num">{fmt_krw(r["spend"])}</td>'
            f'<td class="num">{fmt_int(r["installs"])}</td></tr>'
        )
    return '<table class="mini-table">' + "".join(trs) + "</table>"


def render_analysis_grid(type_breakdown: list, platform_breakdown: list) -> str:
    return (
        '<div class="analysis-grid">'
        '<div class="analysis-card"><h4>🎨 소재 유형별 성과</h4>'
        f'{render_mini_table(type_breakdown)}</div>'
        '<div class="analysis-card"><h4>📱 플랫폼별 성과</h4>'
        f'{render_mini_table(platform_breakdown)}</div>'
        '</div>'
    )


def render_top5_table(creatives: list) -> str:
    if not creatives:
        return ""
    head = (
        '<h3 class="sec-title">💰 Top 5 소재 (지출 기준)</h3>'
        '<div class="ct-wrap"><table class="ct"><thead><tr>'
        '<th class="rank">#</th><th>소재명</th><th>유형</th><th>플랫폼</th>'
        '<th class="num">지출</th><th class="num">설치</th><th class="num">CPI</th>'
        '<th class="num">ROAS</th><th class="num">노출</th></tr></thead><tbody>'
    )
    rows = []
    for i, c in enumerate(creatives[:5], start=1):
        rc = roas_class(c["roas"])
        rows.append(
            f'<tr>{rank_cell(i)}'
            f'<td class="ad-name" title="{esc(c["name"])}">{esc(c["name"])}</td>'
            f'<td>{type_tag(c["type"])}</td>'
            f'<td>{platform_tag(c["platform"])}</td>'
            f'<td class="num">{fmt_krw(c["spend"])}</td>'
            f'<td class="num">{fmt_int(c["installs"])}</td>'
            f'<td class="num">{fmt_int(c["cpi"])}</td>'
            f'<td class="num {rc}">{fmt_roas(c["roas"])}</td>'
            f'<td class="num">{fmt_int(c["impressions"])}</td></tr>'
        )
    return head + "".join(rows) + "</tbody></table></div>"


def render_best_roas_table(creatives: list) -> str:
    if not creatives:
        return ""
    head = (
        '<h3 class="sec-title">🏆 Best ROAS 소재 (지출 1만원 이상, 노출 5만 이상)</h3>'
        '<div class="ct-wrap"><table class="ct"><thead><tr>'
        '<th class="rank">#</th><th>소재명</th><th>유형</th><th>플랫폼</th>'
        '<th class="num">ROAS</th><th class="num">지출</th><th class="num">설치</th>'
        '</tr></thead><tbody>'
    )
    rows = []
    for i, c in enumerate(creatives[:10], start=1):
        rc = roas_class(c["roas"])
        rows.append(
            f'<tr>{rank_cell(i)}'
            f'<td class="ad-name" title="{esc(c["name"])}">{esc(c["name"])}</td>'
            f'<td>{type_tag(c["type"])}</td>'
            f'<td>{platform_tag(c["platform"])}</td>'
            f'<td class="num {rc}">{fmt_roas(c["roas"])}</td>'
            f'<td class="num">{fmt_krw(c["spend"])}</td>'
            f'<td class="num">{fmt_int(c["installs"])}</td></tr>'
        )
    return head + "".join(rows) + "</tbody></table></div>"


def render_best_cpi_table(creatives: list) -> str:
    if not creatives:
        return ""
    head = (
        '<h3 class="sec-title">⚡ Best CPI 효율 소재 (노출 5만 이상)</h3>'
        '<div class="ct-wrap"><table class="ct"><thead><tr>'
        '<th class="rank">#</th><th>소재명</th><th>유형</th><th>플랫폼</th>'
        '<th class="num">CPI</th><th class="num">지출</th><th class="num">설치</th>'
        '<th class="num">노출</th></tr></thead><tbody>'
    )
    rows = []
    for i, c in enumerate(creatives[:10], start=1):
        rows.append(
            f'<tr>{rank_cell(i)}'
            f'<td class="ad-name" title="{esc(c["name"])}">{esc(c["name"])}</td>'
            f'<td>{type_tag(c["type"])}</td>'
            f'<td>{platform_tag(c["platform"])}</td>'
            f'<td class="num">{fmt_int(c["cpi"])}</td>'
            f'<td class="num">{fmt_krw(c["spend"])}</td>'
            f'<td class="num">{fmt_int(c["installs"])}</td>'
            f'<td class="num">{fmt_int(c["impressions"])}</td></tr>'
        )
    return head + "".join(rows) + "</tbody></table></div>"


def render_budget_section(pane_idx: int, comment: str) -> str:
    return (
        '<h3 class="sec-title">📊 예산 플랜 코멘트</h3>'
        '<div class="budget-section">'
        f'<textarea class="budget-textarea" data-game-idx="{pane_idx}" '
        'placeholder="이 게임의 예산 플랜 코멘트를 작성하세요. 입력하면 브라우저에 자동 저장됩니다.">'
        f'{esc(comment)}</textarea>'
        '<div class="budget-hint">💾 자동 저장 (이 브라우저에만 보관)</div>'
        '</div>'
    )


def render_prereg_table(rows: list) -> str:
    head = (
        '<h3 class="sec-title">📝 사전예약 소재 (참고용 — Cost·eCPI만, ROAS 없음)</h3>'
        '<div class="ct-wrap"><table class="ct"><thead><tr>'
        '<th class="rank">#</th><th>소재명</th><th>유형</th><th>플랫폼</th>'
        '<th class="num">지출</th><th class="num">eCPI</th></tr></thead><tbody>'
    )
    trs = []
    for i, r in enumerate(rows[:10], start=1):
        ecpi = r.get("ecpi")
        ecpi_txt = fmt_int(ecpi) if ecpi is not None else "-"
        trs.append(
            f'<tr>{rank_cell(i)}'
            f'<td class="ad-name" title="{esc(r["name"])}">{esc(r["name"])}</td>'
            f'<td>{type_tag(r["type"])}</td>'
            f'<td>{platform_tag(r["platform"])}</td>'
            f'<td class="num">{fmt_krw(r["spend"])}</td>'
            f'<td class="num">{ecpi_txt}</td></tr>'
        )
    return head + "".join(trs) + "</tbody></table></div>"


PREREG_AUX_NOTE = "이 채널에서 사전예약/전환 최적화 캠페인이 정규 캠페인과 함께 운영 중입니다 (참고용, ROAS 미집계)."


def render_prereg_aux_block(aux: dict) -> str:
    """Auxiliary pre-registration reference block appended after the normal
    ranking tables/budget section, for channels running 사전예약 campaigns
    alongside already-launched regular campaigns (REPORT_SPEC.md §5 '보조
    블록'). Distinct from the full-channel status="prereg" mode, which is
    used when a channel has ONLY pre-registration campaigns."""
    note = PREREG_AUX_NOTE
    if aux.get("remap_caveat", True):
        note += PREREG_NOTE_CAVEAT
    metrics = (
        '<div class="mc" style="display:inline-block;margin-right:10px">'
        '<div class="ml">사전예약 지출</div>'
        f'<div class="mv">{fmt_krw(aux["spend"])}</div>'
        f'<div class="ms">{fmt_int(aux["spend"])}원</div></div>'
        '<div class="mc" style="display:inline-block">'
        '<div class="ml">소재수</div>'
        f'<div class="mv">{fmt_int(aux["creative_count"])}개</div></div>'
    )
    return (
        f'<p class="no-data">{note}</p>'
        f'{metrics}'
        f'{render_prereg_table(aux.get("top", []))}'
    )


def render_channel_pane(pane_idx: int, active: bool, channel: dict) -> tuple:
    """Returns (pane_html, chart_data_dict_for_this_pane)."""
    status = channel.get("status", "normal")
    cls = "tab-pane active" if active else "tab-pane"
    chart_data = {
        "top_names": [], "top_spends": [],
        "type_labels": [], "type_spends": [],
        "plat_labels": [], "plat_spends": [],
    }

    if status == "empty":
        body = f'<p class="no-data">{EMPTY_CHANNEL_NOTE}</p>'
        return f'<div class="{cls}" id="pane{pane_idx}">{body}</div>', chart_data

    if status == "prereg":
        note = PREREG_NOTE_SHORT
        if channel.get("remap_caveat", True):
            note += PREREG_NOTE_CAVEAT
        metrics = (
            '<div class="metrics">'
            '<div class="mc"><div class="ml">사전예약 지출</div>'
            f'<div class="mv">{fmt_krw(channel["spend"])}</div>'
            f'<div class="ms">{fmt_int(channel["spend"])}원</div></div>'
            '<div class="mc"><div class="ml">소재수</div>'
            f'<div class="mv">{fmt_int(channel["creative_count"])}개</div></div>'
            '</div>'
        )
        body = metrics + f'<p class="no-data">{note}</p>' + render_prereg_table(channel.get("top", []))
        return f'<div class="{cls}" id="pane{pane_idx}">{body}</div>', chart_data

    # status == "normal"
    m = channel["metrics"]
    parts = [render_metrics_normal(m)]
    parts.append(render_charts_row(pane_idx))
    parts.append(render_analysis_grid(channel["type_breakdown"], channel["platform_breakdown"]))
    parts.append(render_top5_table(channel.get("top5", [])))
    parts.append(render_best_roas_table(channel.get("best_roas", [])))
    parts.append(render_best_cpi_table(channel.get("best_cpi", [])))
    if channel.get("prereg_aux"):
        parts.append(render_prereg_aux_block(channel["prereg_aux"]))
    parts.append(render_budget_section(pane_idx, channel.get("budget_comment", "")))
    body = "".join(parts)

    for c in channel.get("chart_top10", []):
        chart_data["top_names"].append(c["name"])
        chart_data["top_spends"].append(c["spend"])
    for r in channel.get("type_breakdown", []):
        chart_data["type_labels"].append(r["label"])
        chart_data["type_spends"].append(r["spend"])
    for r in channel.get("platform_breakdown", []):
        chart_data["plat_labels"].append(r["label"])
        chart_data["plat_spends"].append(r["spend"])

    return f'<div class="{cls}" id="pane{pane_idx}">{body}</div>', chart_data


def render_game_section(game_idx: int, active: bool, game: dict, pane_counter: list) -> tuple:
    """pane_counter is a 1-item mutable list used as a shared running pane index
    counter across the whole document (matches the reference file's global
    pane0..pane13 numbering, independent of the game index)."""
    sec_cls = "game-section active" if active else "game-section"
    meta_pane_idx = pane_counter[0]
    pane_counter[0] += 1
    google_pane_idx = pane_counter[0]
    pane_counter[0] += 1

    ch_tabs = (
        '<div class="ch-tabs">'
        f'<button class="ch-tab tab-meta active" onclick="showCh({game_idx}, \'meta\', {meta_pane_idx})">Meta</button>'
        f'<button class="ch-tab tab-google" onclick="showCh({game_idx}, \'google\', {google_pane_idx})">Google</button>'
        '</div>'
    )

    meta_pane_html, meta_chart = render_channel_pane(meta_pane_idx, True, game["channels"]["meta"])
    google_pane_html, google_chart = render_channel_pane(google_pane_idx, False, game["channels"]["google"])

    section_html = f'<div class="{sec_cls}" id="game_{game_idx}">{ch_tabs}{meta_pane_html}{google_pane_html}</div>'
    chart_entries = {str(meta_pane_idx): meta_chart, str(google_pane_idx): google_chart}
    return section_html, chart_entries, (meta_pane_idx, google_pane_idx)


# ---------------------------------------------------------------------------
# Top-level assembly
# ---------------------------------------------------------------------------


def generate_html(data: dict) -> str:
    period = data["period"]
    start = datetime.fromisoformat(period["start"])
    end = datetime.fromisoformat(period["end"])
    generated_at = period.get("generated_at")
    if not generated_at:
        generated_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    sub_title = data.get("sub_title", DEFAULT_SUB_TITLE)

    per_text = (
        f"{fmt_period_date(start)} ~ {fmt_period_date(end)} | "
        f"W{iso_week(start)}-W{iso_week(end)}"
    )

    games = data["games"]

    g_tab_buttons = []
    for i, g in enumerate(games):
        active_cls = " active" if i == 0 else ""
        g_tab_buttons.append(
            f'<button class="g-tab{active_cls}" style="--g-color:{esc(g["color"])}" '
            f'onclick="showG({i})" id="gtab_{i}">{esc(g["name"])}</button>'
        )
    g_tabs_html = '<div class="g-tabs">' + "".join(g_tab_buttons) + "\n</div>"

    pane_counter = [0]
    game_sections = []
    chart_data = {}
    for i, g in enumerate(games):
        section_html, chart_entries, _ = render_game_section(i, i == 0, g, pane_counter)
        game_sections.append(section_html)
        chart_data.update(chart_entries)

    total_panes = pane_counter[0]

    ctn_html = '<div class="ctn">' + g_tabs_html + "".join(game_sections) + "\n</div>"

    # Report id used as the localStorage namespace for budget comment
    # autosave, matching the reference file's convention of using the
    # report's own filename (without extension) as REPORT_ID.
    report_id = data.get(
        "report_id",
        f"SuperPlanet_Meta_Google_성과보고서_{start.strftime('%y%m%d')}-{end.strftime('%y%m%d')}",
    )

    data_json = json.dumps(chart_data, ensure_ascii=False)

    script = f"""
const DATA = {data_json};
const typeColors = {json.dumps(TYPE_CHART_COLORS)};
const platColors = {json.dumps(PLAT_CHART_COLORS)};
const barColor = '{BAR_CHART_COLOR}';

function fmtKRW(v) {{
  if (v >= 100000000) return (v/100000000).toFixed(1) + '억';
  if (v >= 10000) return (v/10000).toLocaleString() + '만';
  return v.toLocaleString();
}}

// Level 1: 게임 탭 전환
function showG(bIdx) {{
  document.querySelectorAll('.g-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.game-section').forEach(s => s.classList.remove('active'));
  document.getElementById('gtab_' + bIdx).classList.add('active');
  document.getElementById('game_' + bIdx).classList.add('active');
}}
// Level 2: 채널 서브탭 전환 (게임 섹션 내부)
function showCh(bIdx, ch, paneIdx) {{
  const sec = document.getElementById('game_' + bIdx);
  if (!sec) return;
  sec.querySelectorAll('.ch-tab').forEach(b => b.classList.remove('active'));
  sec.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  const chBtn = sec.querySelector('.ch-tab.tab-' + ch);
  if (chBtn) chBtn.classList.add('active');
  const pn = document.getElementById('pane' + paneIdx);
  if (pn) pn.classList.add('active');
}}
// Legacy alias (안 쓰이지만 호환용)
function showTab(idx) {{ /* deprecated */ }}

for (let i = 0; i < {total_panes}; i++) {{
  const d = DATA[String(i)];
  if (!d) continue;

  const barEl = document.getElementById('bar_' + i);
  if (barEl && d.top_names.length > 0) {{
    new Chart(barEl, {{
      type: 'bar',
      data: {{ labels: d.top_names, datasets: [{{ data: d.top_spends, backgroundColor: barColor, borderRadius: 4 }}] }},
      options: {{
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Top 10 소재 (지출)', font: {{ size: 12 }} }}, legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: function(ctx) {{ return fmtKRW(ctx.raw) + '원'; }} }} }} }},
        scales: {{ x: {{ ticks: {{ callback: function(v) {{ return fmtKRW(v); }} }} }}, y: {{ ticks: {{ font: {{ size: 10 }} }} }} }}
      }}
    }});
  }}

  const typeEl = document.getElementById('type_' + i);
  if (typeEl && d.type_labels.length > 0) {{
    new Chart(typeEl, {{
      type: 'doughnut',
      data: {{ labels: d.type_labels, datasets: [{{ data: d.type_spends, backgroundColor: typeColors.slice(0, d.type_labels.length) }}] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: '소재 유형별 지출', font: {{ size: 12 }} }}, legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
          tooltip: {{ callbacks: {{ label: function(ctx) {{ const t = ctx.dataset.data.reduce((a,b) => a+b, 0); return ctx.label + ': ' + fmtKRW(ctx.raw) + '원 (' + (t>0?((ctx.raw/t)*100).toFixed(1):0) + '%)'; }} }} }} }}
      }}
    }});
  }}

  const platEl = document.getElementById('plat_' + i);
  if (platEl && d.plat_labels.length > 0) {{
    new Chart(platEl, {{
      type: 'doughnut',
      data: {{ labels: d.plat_labels, datasets: [{{ data: d.plat_spends, backgroundColor: platColors.slice(0, d.plat_labels.length) }}] }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: '플랫폼별 지출', font: {{ size: 12 }} }}, legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }} }} }},
          tooltip: {{ callbacks: {{ label: function(ctx) {{ const t = ctx.dataset.data.reduce((a,b) => a+b, 0); return ctx.label + ': ' + fmtKRW(ctx.raw) + '원 (' + (t>0?((ctx.raw/t)*100).toFixed(1):0) + '%)'; }} }} }} }}
      }}
    }});
  }}
}}

// ─── Budget comment textarea: localStorage 자동 저장/복원 ───
const REPORT_ID = "{report_id}";
document.querySelectorAll('.budget-textarea').forEach(function(ta) {{
  const key = 'budget_comment::' + REPORT_ID + '::' + ta.dataset.gameIdx;
  try {{
    const saved = localStorage.getItem(key);
    if (saved !== null) ta.value = saved;
  }} catch (e) {{}}
  ta.addEventListener('input', function() {{
    try {{ localStorage.setItem(key, ta.value); }} catch (e) {{}}
  }});
}});
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SuperPlanet 광고 소재 성과 보고서</title>
<script src="{CHARTJS_CDN_URL}"></script>
<style>{STYLE_BLOCK}</style>
</head>
<body>
<div id="pw-gate" style="position:fixed;inset:0;z-index:99999;background:#1a1a2e;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
  <div style="background:#16213e;border-radius:16px;padding:48px 40px;box-shadow:0 8px 32px rgba(0,0,0,.4);text-align:center;max-width:380px;width:90%">
    <div style="font-size:48px;margin-bottom:16px">&#x1F512;</div>
    <h2 style="color:#e2e8f0;margin:0 0 8px;font-size:20px">보고서 열람</h2>
    <p style="color:#94a3b8;margin:0 0 24px;font-size:14px">비밀번호를 입력하세요</p>
    <input id="pw-input" type="password" placeholder="Password"
      style="width:100%;padding:12px 16px;border:2px solid #334155;border-radius:8px;background:#0f172a;color:#e2e8f0;font-size:16px;outline:none;box-sizing:border-box;transition:border .2s"
      onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='#334155'">
    <p id="pw-err" style="color:#ef4444;margin:8px 0 0;font-size:13px;min-height:20px"></p>
    <button onclick="checkPw()"
      style="margin-top:16px;width:100%;padding:12px;background:#3b82f6;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;transition:background .2s"
      onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">확인</button>
  </div>
</div>
<style>#pw-gate~*:not(script){{display:none!important}}</style>
<script>
var PW_HASH="{PW_HASH}";
async function sha256(m){{var e=new TextEncoder().encode(m);var h=await crypto.subtle.digest("SHA-256",e);return Array.from(new Uint8Array(h)).map(b=>b.toString(16).padStart(2,"0")).join("")}}
async function checkPw(){{var v=document.getElementById("pw-input").value;var h=await sha256(v);if(h===PW_HASH){{document.getElementById("pw-gate").remove();document.querySelectorAll("style").forEach(s=>{{if(s.textContent.includes("pw-gate"))s.remove()}})}}else{{document.getElementById("pw-err").textContent="비밀번호가 올바르지 않습니다."}}}}
document.addEventListener("keydown",function(e){{if(e.key==="Enter"&&document.getElementById("pw-gate"))checkPw()}});
</script>

<div class="hdr">
  <h1>SuperPlanet 광고 소재 성과 보고서</h1>
  <div class="sub">{esc(sub_title)}</div>
  <div class="per">{esc(per_text)}</div>
</div>
{ctn_html}
<div class="ft">
  SuperPlanet 광고 소재 성과 보고서 | {esc(per_text)}<br>
  Generated {esc(generated_at)}
</div>
<script>
{script}
</script>
</body>
</html>"""

    return html_doc


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv):
    if len(argv) < 3:
        print("Usage: python3 generate_report.py <data.json> <out.html>", file=sys.stderr)
        return 1
    with open(argv[1], encoding="utf-8") as f:
        data = json.load(f)
    html_out = generate_html(data)
    with open(argv[2], "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Wrote {argv[2]} ({len(html_out)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
