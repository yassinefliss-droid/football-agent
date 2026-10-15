# One image = code + database + vector index, so the container starts instantly.
FROM python:3.11-slim

# Hugging Face Spaces runs containers as user 1000: create it so the app can write its files.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/home/user/app/.cache/fastembed
WORKDIR /home/user/app

# Dependencies first: this layer is cached as long as requirements.txt does not change.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user app app
COPY --chown=user scripts scripts
COPY --chown=user eval eval

# Build the data at image build time (downloads the CSVs, Wikipedia articles and embedding models).
RUN python scripts/download_data.py \
 && python scripts/build_db.py \
 && python scripts/build_wiki_corpus.py \
 && python scripts/build_index.py

EXPOSE 7860
CMD ["streamlit", "run", "app/ui.py", "--server.port=7860", "--server.address=0.0.0.0"]
