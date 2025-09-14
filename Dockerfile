FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY . .

# Ensure web interface is available
RUN mkdir -p static && cp web/index.html static/ && cp web/rules.html static/ 2>/dev/null || echo "Web submodule not available, using fallback"

EXPOSE 8090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]