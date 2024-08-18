# Start from the base image
FROM iwaseyusuke/ryu-mininet

# Install system dependencies for Python
USER root
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libsqlite3-dev \
    libreadline-dev \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.10.4
RUN wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz \
    && tar -xvf Python-3.10.4.tgz \
    && cd Python-3.10.4 \
    && ./configure --enable-optimizations \
    && make \
    && make install \
    && cd .. \
    && rm -rf Python-3.10.4 Python-3.10.4.tgz

# Set the default Python version to 3.10.4
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1 \
    && python --version \
    && pip install --upgrade pip

# Copy the application code into the Docker image
COPY . /app/

# Install Python dependencies
RUN pip install -r /app/requirements.txt

# Set the working directory
WORKDIR /app

# Default command (you can modify this as needed)
CMD ["/bin/bash"]
