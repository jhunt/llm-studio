FROM python:3.14
WORKDIR /app

RUN apt-get update \
 && apt-get install -y sqlite3 \
 && apt-get clean

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY . .
ENTRYPOINT ["/app/entrypoint.sh"]

VOLUME /data

ENV OLLAMA_HOST=http://127.0.0.1:11434
ENV OLLAMA_MODEL=llama3.2

EXPOSE 5000
ENV PORT=5000

ENV LLM_STUDIO_DB=/data/studio.db
