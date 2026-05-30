"""
LINE 公式アカウント（Messaging API）経由でプッシュメッセージを送るスクリプト。

前提: 送付先があなたの公式アカウントを友だち追加していること。
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

DEFAULT_MESSAGE = "テストメッセージです。"


def _write_last_run(exit_code: int, summary: str) -> None:
    """ターミナル以外でも結果を残す（同じフォルダの last_run.txt）。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"[{ts}] exit={exit_code}\n{summary}\n"
    path = Path(__file__).resolve().parent / "last_run.txt"
    path.write_text(body, encoding="utf-8")


def _print_run_header() -> None:
    """
    直前のエラー表示が残ったまま「何も出ない」ように見えるのを防ぐ。
    消したくない場合は環境変数 LINE_NO_CLEAR=1
    """
    if os.environ.get("LINE_NO_CLEAR") != "1":
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 58, flush=True)
    print(f" send_line_message.py  実行 {ts}", flush=True)
    print("=" * 58, flush=True)


def main() -> int:
    _print_run_header()

    # カレントディレクトリがどこでも、スクリプトと同じフォルダの .env を読む
    load_dotenv(Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(
        description="LINE 公式アカウント（Messaging API）に登録したユーザーへテキストを送信します。",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="送る文章（未指定なら環境変数 LINE_MESSAGE、それもなければデフォルト文）",
    )
    parser.add_argument(
        "-u",
        "--user-id",
        help="送信先のユーザーID（未指定なら環境変数 LINE_USER_ID）",
    )
    args = parser.parse_args()

    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    user_id = (args.user_id or os.getenv("LINE_USER_ID", "")).strip()
    text = (args.message or os.getenv("LINE_MESSAGE") or DEFAULT_MESSAGE).strip()

    if not token:
        msg = (
            "エラー: 環境変数 LINE_CHANNEL_ACCESS_TOKEN が空です。"
            " .env ファイルを作成し、トークンを設定してください。"
        )
        print(msg, file=sys.stderr, flush=True)
        _write_last_run(1, msg)
        return 1
    if not user_id:
        msg = (
            "エラー: 送信先のユーザーIDがありません。"
            " 環境変数 LINE_USER_ID を設定するか、--user-id で指定してください。"
        )
        print(msg, file=sys.stderr, flush=True)
        _write_last_run(1, msg)
        return 1

    api = LineBotApi(token)
    try:
        api.push_message(user_id, TextSendMessage(text=text))
    except LineBotApiError as e:
        print(f"送信に失敗しました: {e}", file=sys.stderr, flush=True)
        parts = [f"送信に失敗しました: {e}"]
        if e.status_code is not None:
            print(f"HTTP ステータス: {e.status_code}", file=sys.stderr, flush=True)
            parts.append(f"HTTP ステータス: {e.status_code}")
        if e.error is not None:
            print(f"詳細: {e.error}", file=sys.stderr, flush=True)
            parts.append(f"詳細: {e.error}")
        _write_last_run(1, "\n".join(parts))
        return 1

    ok = "送信に成功しました。"
    print(ok, flush=True)
    _write_last_run(0, ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
