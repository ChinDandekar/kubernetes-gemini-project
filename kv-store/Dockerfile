# Base image with Python
FROM python:3.12.7-alpine

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt for dependency installation
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose the port your app runs on
EXPOSE 8080

# Define the command to run the app
CMD ["python", "kv-store.py"]
