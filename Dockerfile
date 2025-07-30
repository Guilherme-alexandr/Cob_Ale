FROM python:3.11-slim-bullseye


WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000

CMD ["python", "run.py"]
