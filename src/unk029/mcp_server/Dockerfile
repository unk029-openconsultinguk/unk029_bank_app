FROM python:3.12-slim

WORKDIR /app

# Copy the requirements from mcp_server directory
COPY mcp_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files (accounts.py, mcpserver.py, etc.)
COPY . .

# Set PYTHONPATH to include current directory
ENV PYTHONPATH=/app:$PYTHONPATH

CMD ["python", "-m", "uvicorn", "mcp_server.main:app", "--host", "0.0.0.0", "--port", "8002"]
