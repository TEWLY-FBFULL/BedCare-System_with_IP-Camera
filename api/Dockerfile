FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-dev \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/bin/python
RUN ln -sf /usr/bin/pip3 /usr/bin/pip

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir onnxruntime-gpu==1.19.0

RUN pip install --no-cache-dir -r requirements.txt

RUN pip uninstall -y protobuf mediapipe onnx ultralytics && \
    pip install --no-cache-dir "protobuf<4" "mediapipe==0.10.11" "ultralytics==8.4.9" "onnx==1.16.0"

ENV SYNC_COMMAND=0
ENV ULTRALYTICS_OFFLINE=True

COPY app ./app
RUN which uvicorn || echo "Uvicorn not found in PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]