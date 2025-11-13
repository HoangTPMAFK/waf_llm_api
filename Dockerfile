FROM python:3.11-alpine

RUN apk update && apk add sqlite

WORKDIR /ml_detector

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]