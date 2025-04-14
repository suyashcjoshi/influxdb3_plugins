FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY fastAPIConnect.py /app/

EXPOSE 8001

CMD ["uvicorn", "fastAPIConnect:app", "--host", "0.0.0.0", "--port", "8001"]
