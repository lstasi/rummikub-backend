FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY . .

# Install make utility for build process
RUN apt-get update && apt-get install -y make

# Build static files from web submodule
RUN make copy-static

EXPOSE 8090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]