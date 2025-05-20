# Deploying to Render

This repository is configured for deployment on [Render](https://render.com/). Follow these steps to deploy the application:

## Prerequisites

1. A Render account
2. A Git repository containing your application code

## Deployment Steps

### Option 1: Using render.yaml (Blueprint)

1. Fork or clone this repository to your own GitHub account.
2. In the Render dashboard, click on "New" and select "Blueprint".
3. Connect your GitHub account if you haven't already.
4. Select the repository containing this application.
5. Render will automatically detect the `render.yaml` file and create all the required services.
6. Follow the prompts to complete the deployment.

### Option 2: Manual Setup

If you prefer to set up your services manually:

1. **Web Service**:
   - Create a new Web Service in Render
   - Connect your Git repository
   - Use Docker runtime
   - Set the Dockerfile path to `./Dockerfile`
   - Set the following environment variables:
     - `FLASK_APP=manage.py`
     - `FLASK_ENV=production`
     - `FLASK_CONFIG=production`
     - `PORT=10000` (Render will override this with its own PORT)
     - `SECRET_KEY` (generate a secure random string)
   - Set the health check path to `/health`

2. **Worker Service**:
   - Create a new Background Worker in Render
   - Connect your Git repository
   - Use Docker runtime
   - Set the Dockerfile path to `./Dockerfile.worker`
   - Set environment variables to match those in your Web Service

3. **Database**:
   - Create a new PostgreSQL database in Render
   - Note the connection string for use in your Web and Worker services

4. **Redis**:
   - Create a new Redis instance in Render
   - Note the connection string for use in your Web and Worker services

## Local Development

For local development, you can use Docker Compose:

```bash
docker-compose up
```

This will start the server, worker, PostgreSQL database, Redis, and Adminer services.

- The web application will be available at http://localhost:5000
- The Adminer database UI will be available at http://localhost:8080

## Environment Variables

The following environment variables are required:

- `DATABASE_URL`: PostgreSQL connection string
- `REDISTOGO_URL`: Redis connection string
- `SECRET_KEY`: Secret key for Flask sessions
- `PORT`: Port to run the application on (default: 5000)
- `FLASK_ENV`: Application environment (default: production)
- `FLASK_APP`: Application entry point (default: manage.py)
