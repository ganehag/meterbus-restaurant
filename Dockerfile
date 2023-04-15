# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Create a new user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy the requirements.txt file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the application code into the container
COPY server.py server.py

# Change ownership of the /app directory to the new user
RUN chown -R appuser:appgroup /app

# Install Waitress server
RUN pip install waitress

# Expose the port the app runs on
EXPOSE 8080

# Switch to the new user
USER appuser

# Define the command to run your app using Waitress
CMD ["waitress-serve", "--port=8080", "server:app"]
