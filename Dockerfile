# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Phoenix MCP server globally to drastically speed up Auditor Agent spin-up time
RUN npm install -g @arizeai/phoenix-mcp@latest

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# HuggingFace requires running as non-root user 1000
RUN useradd -m -u 1000 user

# Create directories for Phoenix and DB, and give permissions to user
RUN mkdir -p /app /home/user/.phoenix && chown -R user:user /app /home/user

# Copy application code
COPY --chown=user:user . /app

# Switch to the non-root user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set environment variables for HuggingFace Spaces
# Spaces uses port 7860 by default
ENV PORT=7860
# Set Phoenix to run on a different internal port
ENV PHOENIX_PORT=6006
# Tell tracing to use the internal Phoenix endpoint
ENV PHOENIX_COLLECTOR_ENDPOINT=http://127.0.0.1:6006

# Expose the port HuggingFace expects
EXPOSE 7860

# Create a startup script
RUN echo '#!/bin/bash\n\
# Start the local Open-Source Phoenix Server in the background\n\
python -m phoenix.server.main serve --host 0.0.0.0 --port 6006 &\n\
\n\
# Wait for Phoenix to start\n\
sleep 5\n\
\n\
# Start the FastAPI application on the port HuggingFace expects\n\
uvicorn tracepilot.api:app --host 0.0.0.0 --port 7860\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]
