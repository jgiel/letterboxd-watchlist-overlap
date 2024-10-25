# Set base image (host OS)
FROM python:3.12-alpine

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .
# COPY letterboxd_scraper.py

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY app.py letterboxd_scraper.py ./
COPY templates/*.html templates/

# Specify the command to run on container start
CMD [ "python", "./app.py" ]

