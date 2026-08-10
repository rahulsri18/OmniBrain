FROM python:3.11-slim

WORKDIR /app

# Install dependencies if you have a requirements.txt in frontend,
# otherwise it will install streamlit directly
COPY requirements*.txt ./
RUN pip install --no-cache-dir --default-timeout=300 --retries=10 -r requirements.txt && pip install --no-cache-dir --default-timeout=300 --retries=10 streamlit

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]