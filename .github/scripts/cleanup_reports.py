"""
만료된 보고서 자동 삭제 스크립트 (GitHub Actions용)
====================================================
_report_registry.json을 읽어 TTL이 지난 HTML 보고서를 삭제합니다.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = REPO_ROOT / "_report_registry.json"
CONFIG_FILE = REPO_ROOT / "meta-ad-report" / "scripts" / "publish_config.json"
DEFAULT_TTL_HOURS = 8


def load_json(path: Path) -> dict | list:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    # TTL 설정 로드
    config = load_json(CONFIG_FILE) if CONFIG_FILE.exists() else {}
    ttl_hours = config.get("report_ttl_hours", DEFAULT_TTL_HOURS)

    # 레지스트리 로드
    entries = load_json(REGISTRY_FILE)
    if not entries:
        print("레지스트리가 비어있습니다. 삭제할 보고서 없음.")
        return

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=ttl_hours)

    keep = []
    removed = []

    for entry in entries:
        published_at = datetime.fromisoformat(entry["published_at"])
        filename = entry["filename"]
        file_path = REPO_ROOT / filename

        if published_at < cutoff:
            # 만료 → 파일 삭제
            if file_path.exists():
                file_path.unlink()
                elapsed = now - published_at
                hours = elapsed.total_seconds() / 3600
                print(f"🗑️  삭제: {filename} (게시 후 {hours:.1f}시간 경과)")
                removed.append(filename)
            else:
                print(f"⚠️  파일 없음 (이미 삭제됨): {filename}")
        else:
            remaining = published_at + timedelta(hours=ttl_hours) - now
            hours_left = remaining.total_seconds() / 3600
            print(f"✅ 유지: {filename} (삭제까지 {hours_left:.1f}시간 남음)")
            keep.append(entry)

    # 레지스트리 업데이트 (만료된 항목 제거)
    save_json(REGISTRY_FILE, keep)

    print(f"\n결과: {len(removed)}개 삭제, {len(keep)}개 유지")


if __name__ == "__main__":
    main()
