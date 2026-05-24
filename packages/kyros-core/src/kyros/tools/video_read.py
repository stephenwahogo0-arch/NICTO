import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from kyros.tools.base import Tool


async def tool_video_read(url: str) -> str:
    """
    Read a video from a URL and provide a summary of its content.
    Currently supports YouTube videos via transcript extraction.
    For other platforms, attempts to download audio and transcribe (requires additional dependencies).
    """
    try:
        # Check if it's a YouTube URL
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        youtube_match = re.match(youtube_regex, url)

        if youtube_match:
            video_id = youtube_match.group(6)
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                # Try to get transcript in English first
                ytt_api = YouTubeTranscriptApi()
                transcript_list = ytt_api.fetch(video_id, languages=['en'])
                # Join all transcript text
                full_text = " ".join([snippet.text for snippet in transcript_list.snippets])
                # Simple extractive summary: take first 3 sentences
                sentences = [s.strip() for s in full_text.split('.') if s.strip()]
                summary = '. '.join(sentences[:3])
                if not summary:
                    summary = full_text[:200] + "..." if len(full_text) > 200 else full_text
                return f"Video Summary (YouTube): {summary}"
            except Exception as e:
                # Fallback: try to get transcript in any language
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.fetch(video_id)
                    full_text = " ".join([snippet.text for snippet in transcript_list.snippets])
                    sentences = [s.strip() for s in full_text.split('.') if s.strip()]
                    summary = '. '.join(sentences[:3])
                    if not summary:
                        summary = full_text[:200] + "..." if len(full_text) > 200 else full_text
                    return f"Video Summary (YouTube, auto-translated): {summary}"
                except Exception as e2:
                    return f"Could not retrieve YouTube transcript: {str(e2)}. Please ensure the video has captions available."
        else:
            # For non-YouTube URLs, attempt to download and transcribe
            # This requires yt-dlp and speech_recognition
            try:
                import yt_dlp
                import speech_recognition as sr
                from pydub import AudioSegment
            except ImportError:
                return (
                    "Video reading for non-YouTube URLs requires additional dependencies. "
                    "Please install: yt-dlp, SpeechRecognition, and pydub. "
                    "Alternatively, provide a YouTube URL for transcript-based summary."
                )

            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                audio_file = tmpdir_path / "audio.wav"

                # Download audio using yt-dlp
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                        'preferredquality': '192',
                    }],
                    'outtmpl': str(tmpdir_path / 'audio.%(ext)s'),
                    'quiet': True,
                }
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as e:
                    return f"Failed to download video: {str(e)}"

                # Find the downloaded audio file (yt-dlp may change extension)
                audio_files = list(tmpdir_path.glob("audio.*"))
                if not audio_files:
                    return "Failed to locate downloaded audio file."
                audio_file = audio_files[0]

                # Convert to wav if needed (SpeechRecognition works best with wav)
                if audio_file.suffix.lower() != '.wav':
                    try:
                        sound = AudioSegment.from_file(audio_file)
                        wav_file = tmpdir_path / "audio.wav"
                        sound.export(wav_file, format="wav")
                        audio_file = wav_file
                    except Exception as e:
                        return f"Failed to convert audio to wav: {str(e)}"

                # Transcribe audio
                recognizer = sr.Recognizer()
                try:
                    with sr.AudioFile(str(audio_file)) as source:
                        audio_data = recognizer.record(source)
                    # Try Google Speech Recognition (free tier, may have limits)
                    text = recognizer.recognize_google(audio_data)
                except sr.RequestError:
                    # Fallback to offline recognition if available
                    try:
                        text = recognizer.recognize_sphinx(audio_data)
                    except Exception as e:
                        return f"Speech recognition failed: {str(e)}. Please check audio quality and try again."
                except sr.UnknownValueError:
                    return "Speech recognition could not understand the audio."

                # Summarize the transcription
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                summary = '. '.join(sentences[:3])
                if not summary:
                    summary = text[:200] + "..." if len(text) > 200 else text
                return f"Video Summary: {summary}"

    except Exception as e:
        return f"Error processing video: {str(e)}"


VideoReadTool = Tool(
    name="video_read",
    description="Read and summarize video content from URLs (YouTube, Instagram, Facebook, etc.). Extracts transcript or downloads and transcribes audio to generate a summary.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the video to read and summarize"}
        },
        "required": ["url"],
    },
    async_function=tool_video_read,
)