FROM python:3.11-slim  
WORKDIR /app  
RUN apt-get update && apt-get install -y libreoffice libreoffice-writer ure libreoffice-java-common libreoffice-core libreoffice-common fonts-liberation && rm -rf /var/lib/apt/lists/*  
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt  
COPY . .  
EXPOSE 10000  
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"] 
