FROM python:3.8-alpine

# Packages required for psycopg2 and WeasyPrint dependencies
RUN apk update && apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    make \
    # WeasyPrint dependencies
    pango \
    cairo \
    fontconfig \
    ttf-dejavu \
    # Additional build dependencies
    build-base

# Install Gunicorn for production serving
RUN pip install gunicorn

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
ENV PYTHONIOENCODING=UTF-8
RUN pip3 install --no-cache-dir sqlalchemy_utils==0.38.3 flask_dance==5.1.0 Flask-Caching==1.11.1 python-gitlab==3.10.0

# Copy the rest of the application
COPY . /app

# Set environment variables - these will be overridden by Render
ENV FLASK_APP=manage.py
ENV FLASK_ENV=production

# Run migrations and start the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers=2 --threads=4 manage:app

