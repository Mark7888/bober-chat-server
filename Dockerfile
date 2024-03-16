# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory to /app
WORKDIR /app

# copy requirements.txt
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 8000 available to the world outside this container
EXPOSE 8088

# Define environment variable
ENV FLASK_APP main.py

# Run flask when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8088", "main:app"]
