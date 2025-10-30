# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.13.2
FROM python:${PYTHON_VERSION}-slim as backend
# We also install curl
RUN apt-get -y update; apt-get -y install curl graphviz

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the source code into the container.
COPY . .

RUN python -m pip install -r requirements-freeze.txt

# Expose the port that the application listens on.
EXPOSE 8080

# Run the application
CMD python -m streamlit run ekiden.py \
        --browser.serverAddress="0.0.0.0" \
        --server.port 8080 \
        --server.headless true \
        --server.enableCORS True \
        --browser.gatherUsageStats false
