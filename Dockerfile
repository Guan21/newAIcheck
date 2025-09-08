FROM python:3.11-slim

WORKDIR /workspace

COPY . /workspace

RUN pip install --upgrade pip && \
    pip install -r requirements.txt || true

# ログ保存用ディレクトリ
RUN mkdir -p /workspace/logs

CMD ["bash"]
