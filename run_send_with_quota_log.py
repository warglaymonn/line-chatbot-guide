"""
発展用: プッシュ送信（send_line_message.main）のあと、
月間メッセージ枠（GET /v2/bot/message/quota 等）を取得し、
ターミナル表示 + send_quota.log へ追記する。

参考: https://developers.line.biz/ja/reference/messaging-api/#get-quota
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError

import send_line_message

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_PATH = SCRIPT_DIR / "send_quota.log"


def _append_log_line(text: str) -> None:
    """ターミナルとログの両方へ同じ1行を出す。"""
    print(text, flush=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")


def _format_quota_line_and_remaining(api: LineBotApi) -> tuple[str, int | None]:
    """
    月間の「上限」と「今月の送信数」から残り目安を文面化する。
    戻り値の残りは limited かつ上限値ありのときのみ int、それ以外は None。
    """
    q = api.get_message_quota()
    c = api.get_message_quota_consumption()
    usage = int(c.total_usage or 0)

    if q.type == "limited":
        limit = q.value
        if limit is None:
            return (
                f"クォータ種別=limited だが上限値なし / "
                f"今月の送信数={usage}",
                None,
            )
        remaining = max(0, int(limit) - usage)
        return (
            f"月間メッセージ上限={limit} / "
            f"今月の送信数={usage} / "
            f"残り目安={remaining}",
            remaining,
        )

    return (
        f"クォータ種別={q.type}（上限値はlimited時のみ数値取得） / "
        f"今月の送信数={usage}",
        None,
    )


def _warning_for_remaining(remaining: int) -> str:
    """
    残り送信目安に応じた注意文（無料枠のイメージで段階表示）。
    区分は排他的: >500 / 300～500 / 101～299 / 100以下
    """
    if remaining > 500:
        return "【月間枠】まだ余裕があります。"
    if 300 <= remaining <= 500:
        return "【月間枠】半分を切りました。"
    if 101 <= remaining <= 299:
        return "【月間枠】気を付けてください。"
    return "【月間枠】あとわずかです。"


def main() -> int:
    load_dotenv(SCRIPT_DIR / ".env")

    print("=" * 58, flush=True)
    print(" run_send_with_quota_log.py（送信 → 枠取得）", flush=True)
    print("=" * 58, flush=True)

    # send_line_message が cls すると上の見出しが消えるので抑止
    os.environ["LINE_NO_CLEAR"] = "1"
    exit_code = send_line_message.main()

    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token:
        _append_log_line("クォータ取得スキップ: LINE_CHANNEL_ACCESS_TOKEN なし")
        return exit_code

    api = LineBotApi(token)
    try:
        line, remaining = _format_quota_line_and_remaining(api)
        _append_log_line(f"[送信終了 exit={exit_code}] {line}")
        if remaining is not None:
            warn = _warning_for_remaining(remaining)
            _append_log_line(warn)
    except LineBotApiError as e:
        _append_log_line(f"[送信終了 exit={exit_code}] クォータ取得に失敗: {e}")

    print("---", flush=True)
    print(f"ログファイル: {LOG_PATH}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
