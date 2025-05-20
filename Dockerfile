FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # psycopg2 dependencies
    postgresql-client \
    libpq-dev \
    # Build dependencies
    build-essential \
    gcc \
    python3-dev \
    # libffi for cffi
    libffi-dev \
    # pkgconfig
    pkg-config \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libcairo2-dev \
    libfontconfig1 \
    fonts-dejavu \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Gunicorn for production serving
RUN pip install gunicorn

# Create and set working directory
WORKDIR /app

# Install pip and upgrade
RUN pip install --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Create a modified requirements file without problematic dependencies
RUN cat requirements.txt | grep -v "^jsmin==" > requirements_modified.txt && \
    # Remove strict version constraints for problem packages
    sed -i 's/^Werkzeug==0.15.5/Werkzeug>=0.15.5,<2.0.0/' requirements_modified.txt && \
    sed -i 's/^python-gitlab==3.10.0/python-gitlab>=3.0.0/' requirements_modified.txt

# Install dependencies in stages
RUN pip install --no-cache-dir wheel setuptools
RUN pip install --no-cache-dir -r requirements_modified.txt
# Install problematic packages separately with looser constraints
RUN pip install jsmin
ENV PYTHONIOENCODING=UTF-8

# Copy the rest of the application
COPY . /app

# Set environment variables - these will be overridden by Render
ENV FLASK_APP=manage.py
ENV FLASK_ENV=production
ENV SQLALCHEMY_TRACK_MODIFICATIONS=False

# Expose port for Render
EXPOSE 8000

# Set health check command
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

# Run migrations and start the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers=2 --threads=4 --timeout=60 manage:app

