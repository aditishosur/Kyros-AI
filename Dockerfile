FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PULSEOPS_API_URL=http://localhost:8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python data/generate_data.py

EXPOSE 8000 8501
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501"]

