"""
にほんごの根っこ活字堂 — 音声一括生成スクリプト(Google Cloud TTS)

使い方:
  1. pip install requests
  2. 環境変数 GOOGLE_TTS_API_KEY に取得したAPIキーをセット
       export GOOGLE_TTS_API_KEY="ここにキー"
  3. このファイルを index.html と同じフォルダに置いて実行
       python3 generate_audio.py

既に生成済みの音声ファイル(audio/{id}.mp3)はスキップされるので、
新しいユニットを追加するたびに再実行すれば、新しい分だけ追加生成されます。
"""

import re, json, os, sys, time, base64
import requests

API_KEY = os.environ.get("GOOGLE_TTS_API_KEY")
INDEX_HTML = "index.html"
OUTPUT_DIR = "audio"

# 声の候補(必要に応じて変更してください):
#   ja-JP-Wavenet-B / C  — 自然な女性/男性声(WaveNet, $4/100万文字)
#   ja-JP-Wavenet-D      — 男性声
#   ja-JP-Neural2-B / C / D — さらに自然だが割高($16/100万文字)
VOICE_NAME = "ja-JP-Wavenet-B"


def load_phrases():
    with open(INDEX_HTML, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"const RAW = (\{.*?\}); //", content, re.S)
    if not m:
        print("ERROR: index.html 内に RAW データが見つかりませんでした。")
        sys.exit(1)
    raw = json.loads(m.group(1))
    phrases = []
    for stage, qs in raw.items():
        for q in qs:
            phrases.append((q["id"], q["target_ja"]))
    return phrases


def synth(text):
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}"
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "ja-JP", "name": VOICE_NAME},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0},
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return base64.b64decode(r.json()["audioContent"])


def main():
    if not API_KEY:
        print("ERROR: 環境変数 GOOGLE_TTS_API_KEY が設定されていません。")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    phrases = load_phrases()
    done = skipped = failed = 0
    total_chars = 0

    for qid, text in phrases:
        out_path = os.path.join(OUTPUT_DIR, f"{qid}.mp3")
        if os.path.exists(out_path):
            skipped += 1
            continue
        try:
            audio = synth(text)
            with open(out_path, "wb") as f:
                f.write(audio)
            done += 1
            total_chars += len(text)
            print(f"OK   {qid}: {text}")
        except Exception as e:
            failed += 1
            print(f"FAIL {qid}: {text} -> {e}")
        time.sleep(0.05)

    print(f"\n完了。新規生成={done}件 / スキップ={skipped}件 / 失敗={failed}件")
    print(f"今回の課金対象文字数: 約{total_chars}文字")


if __name__ == "__main__":
    main()
