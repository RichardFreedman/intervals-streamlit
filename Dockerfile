# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

# Set the working directory in the container
WORKDIR /app

# Add the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port  8501 available to the world outside this container, since this is Streamlit default
EXPOSE  8501


# make sure it starts
ENTRYPOINT ["streamlit", "run", "intervals_streamtlit2.py", "--server.port=8501", "--server.address=0.0.0.0"]



