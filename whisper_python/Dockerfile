FROM onerahmet/openai-whisper-asr-webservice:latest-gpu

COPY requirements.txt .

RUN /app/.venv/bin/pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "/app/.venv/bin/python", "app.py" ]