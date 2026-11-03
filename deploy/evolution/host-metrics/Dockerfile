FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.1.2
COPY app.py .
EXPOSE 9100
CMD ["python", "app.py"]
