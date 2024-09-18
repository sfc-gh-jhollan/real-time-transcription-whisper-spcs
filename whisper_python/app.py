import os
from flask import Flask, Response
import numpy as np
import whisper
import ffmpeg
import json  # For JSON handling
import torch
from flask import request, jsonify
import requests
import json
import snowflake.connector
from snowflake.snowpark import Session
from snowflake.cortex import Complete

app = Flask(__name__)
app.static_folder = "static"


from urllib.parse import unquote


def connection() -> snowflake.connector.SnowflakeConnection:
    if os.path.isfile("/snowflake/session/token"):
        creds = {
            "host": os.getenv("SNOWFLAKE_HOST"),
            "port": os.getenv("SNOWFLAKE_PORT"),
            "protocol": "https",
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "authenticator": "oauth",
            "token": open("/snowflake/session/token", "r").read(),
            "warehouse": "xsmall",
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "client_session_keep_alive": True,
        }
    else:
        creds = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "warehouse": "xsmall",
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "client_session_keep_alive": True,
        }

    connection = snowflake.connector.connect(**creds)
    return connection


def call_cortex(transcript: str):
    session = Session.builder.configs({"connection": connection()}).create()
    summary = Complete(
        session=session,
        model="mistral-large",
        prompt=f"""
Given the following transcript of a demo given live for Snowflake, provide a brief summary of the demo.
Focus specifically on the Snowflake features shown. Keep the entire summary very brief, about 50 words.

The person giving the demo's name is Jeff. He works for Snowflake.

The Snowflake features being shown are Snowpark Containers, Hybrid Tables, Relational AI, and Snowflake Cortex.

###
Example summary: "Jeff started with a challenge to do only one demo, and did all three. He showcased Snowpark Container Services for running custom models, Hybrid Tables for real time transactions, and Relational AI for graph analysis. He then showed me, Snowflake Cortex, to summarize a real-time generated transcript. All in Snowflake!"

###
Transcript: {transcript}

             """,
    )
    return summary


model = whisper.load_model(
    "large", device="cuda" if torch.cuda.is_available() else "cpu"
)
options = {"language": "en"}
transcript = ""


@app.route("/audio_upload", methods=["POST"])
def handle_audio_upload():
    audio_file = request.files["audio"]
    audio_format = "webm"  # Update with the actual format of the uploaded audio file
    audio_file.seek(0)
    audio_blob = audio_file.read()
    print(
        f"Received audio file with format {audio_format} and length {len(audio_blob)}"
    )

    if audio_format != "pcm":
        # Convert audio to PCM format
        input_stream = ffmpeg.input("pipe:0", format=audio_format)
        output_stream = ffmpeg.output(
            input_stream, "pipe:1", format="s16le", acodec="pcm_s16le", ar="16000", ac=1
        )
        try:
            audio_pcm, _ = ffmpeg.run(
                output_stream,
                input=audio_blob,
                capture_stdout=True,
                capture_stderr=True,
            )
            print(f"Converted audio to PCM with length {len(audio_pcm)}")

        except ffmpeg.Error as e:
            print(e.stderr)
            return jsonify({"message": "Error converting audio to PCM"})
    else:
        audio_pcm = audio_blob

    audio_buffer = (
        np.frombuffer(audio_pcm, np.int16).flatten().astype(np.float32) / 32768.0
    )
    result = model.transcribe(audio_buffer, **options)
    global transcript
    transcript = transcript + "\n" + result["text"]
    return jsonify(
        {"message": "Audio uploaded successfully", "transcript": result["text"]}
    )


@app.route("/transcript", methods=["GET"])
def get_transcript():
    return transcript


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/reset", methods=["POST"])
def reset():
    global transcript
    transcript = ""
    return jsonify({"message": "Transcript reset successfully"})


@app.route("/generate_summary", methods=["POST"])
def generate_summary():
    global transcript
    summary = call_cortex(transcript)

    return jsonify({"summary": summary})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
