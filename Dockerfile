# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for HuggingFace Spaces
# Spaces uses port 7860 by default
ENV PORT=7860
# Set Phoenix to run on a different internal port
ENV PHOENIX_PORT=6006
# Tell tracing to use the internal Phoenix endpoint
ENV PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006

# Expose the port HuggingFace expects
EXPOSE 7860

# Create a startup script
RUN echo '#!/bin/bash\n\
# Start Phoenix Server in the background\n\
python -m phoenix.server.main serve --port 6006 &\n\
\n\
# Wait a few seconds for Phoenix to initialize\n\
sleep 5\n\
\n\
# Start the FastAPI application on the port HuggingFace expects\n\
uvicorn tracepilot.api:app --host 0.0.0.0 --port 7860\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]
