import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# --- 関数定義 ---
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import streamlit as st

def get_youtube_subtitles(youtube_url):
    try:
        # --- 1. 動画IDの抽出 ---
        parsed_url = urlparse(youtube_url)
        video_id = None

        if parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]
        elif parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                video_id = query_params.get('v', [None])[0]
            elif parsed_url.path.startswith(('/embed/', '/shorts/')):
                video_id = parsed_url.path.split('/')[2]

        if not video_id:
            return None, "動画IDを抽出できませんでした。URLを確認してください。"

        # --- 2. 字幕リストの取得 ---
        # Cookieは使用せず、標準のアクセスを行います
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # --- 3. 字幕の探索（優先順位をつけて取得） ---
        transcript = None
        
        # 優先順位1: 投稿者が手動作成した日本語 ('ja')
        # 優先順位2: 投稿者が手動作成した英語 ('en')
        # 優先順位3: 自動生成された日本語 ('ja')
        
        try:
            # 手動字幕を探す
            transcript = transcript_list.find_transcript(['ja', 'en'])
        except:
            try:
                # 手動がなければ、自動生成の日本語を探す
                transcript = transcript_list.find_generated_transcript(['ja'])
            except:
                # それでもなければ、存在する最初の字幕を日本語に「翻訳」して取得
                try:
                    first_transcript = next(iter(transcript_list))
                    transcript = first_transcript.translate('ja')
                except:
                    return None, "この動画には取得・翻訳可能な字幕が一切ありません。"

        # --- 4. データの取得と返却 ---
        return transcript.fetch(), None

    except Exception as e:
        error_msg = str(e)
        # よくあるエラーメッセージを分かりやすく変換
        if "line 1, column 0" in error_msg:
            return None, "YouTubeから一時的にアクセスを拒否されました。少し時間を置いてから再度お試しください。"
        elif "Subtitles are disabled" in error_msg:
            return None, "この動画は字幕が無効に設定されています。"
        return None, f"エラーが発生しました: {error_msg}"

# --- Streamlit UI部分 ---
st.set_page_config(page_title="YouTube字幕抽出アプリ")
st.title("YouTube字幕抽出アプリ")

youtube_link = st.text_input("YouTubeのURLを入力してください", placeholder="https://www.youtube.com/watch?v=...")

if st.button("字幕を取得する"):
    if youtube_link:
        with st.spinner('字幕を取得中...'):
            subtitles, error = get_youtube_subtitles(youtube_link)
            
            if error:
                st.error(f"エラー: {error}")
                st.info("※字幕が設定されていない動画や、取得が制限されている動画の可能性があります。")
            else:
                # テキストを成形
                full_text = ""
                for segment in subtitles:
                    # タイムスタンプ付きで表示したい場合
                    # full_text += f"[{segment['start']:.2f}] {segment['text']}\n"
                    # テキストのみの場合
                    full_text += f"{segment['text']} "

                st.success("取得完了！")
                st.text_area("取得結果", full_text, height=400)
                
                # ダウンロードボタン
                st.download_button(
                    label="テキストファイルとして保存",
                    data=full_text,
                    file_name="transcript.txt",
                    mime="text/plain"
                )
    else:
        st.warning("URLを入力してください。")