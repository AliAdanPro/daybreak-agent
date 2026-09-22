FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create a non-root user and group for secure execution
RUN groupadd -r daybreak && useradd -r -g daybreak daybreak

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/

# Set strict execution permissions and ownership
RUN chown -R daybreak:daybreak /app && chmod -R 755 /app

# Switch to non-root user
USER daybreak

# Set python path and safe defaults
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to execute the agent locally
CMD ["python", "src/lambda_function.py"]
