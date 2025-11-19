# Flask Message Board

Simple message board application built with Flask and MySQL. Created as part of learning DevOps practices for containerization and AWS deployment.

## What it does

Basic message board where you can post and view messages. Messages are stored in a MySQL database.

## Features

- Message board interface with AJAX
- MySQL database backend
- Health check endpoints for AWS ECS/ALB
- Runs with Gunicorn in production
- Database connection retry logic
- Security headers and CORS setup

## Running Locally

### Prerequisites
- Python 3.9+
- MySQL database
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

3. Create the database:
```sql
CREATE DATABASE flask_app;
USE flask_app;
SOURCE message.sql;
```

4. Run the app:

Development mode:
```bash
export FLASK_ENV=development
python app.py
```

Production mode (recommended):
```bash
export FLASK_ENV=production
gunicorn --config gunicorn.conf.py app:app
```

5. Open http://localhost:5000

## API Endpoints

- `GET /` - Main message board page
- `POST /api/message` - Add a new message
- `GET /health` - Health check (returns 200 if running)
- `GET /ready` - Readiness check (checks DB connection)

## Environment Variables

Required:
- `MYSQL_HOST` - Database host
- `MYSQL_USER` - Database username
- `MYSQL_PASSWORD` - Database password
- `MYSQL_DB` - Database name

Optional (with defaults):
- `MYSQL_PORT` - Database port (default: 3306)
- `FLASK_ENV` - Environment mode (default: production)
- `LOG_LEVEL` - Logging level (default: INFO)
- `CORS_ORIGINS` - CORS allowed origins (default: *)

## Docker

Build:
```bash
docker build -t flask-message-board .
```

Run:
```bash
docker run -d -p 5000:5000 --env-file .env flask-message-board
```

Or with environment variables:
```bash
docker run -d -p 5000:5000 \
  -e MYSQL_HOST=your-db-host \
  -e MYSQL_USER=user \
  -e MYSQL_PASSWORD=pass \
  -e MYSQL_DB=flask_app \
  flask-message-board
```

## Project Structure

```
app/
├── app.py              # Main Flask app
├── config.py           # Config management
├── gunicorn.conf.py    # Gunicorn settings
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container setup
├── message.sql         # Database schema
├── static/
│   └── style.css
└── templates/
    ├── index.html
    └── error.html
```

## AWS Deployment

Designed to run on AWS ECS with:
- RDS MySQL database
- Application Load Balancer
- CloudWatch logging
- Auto-scaling

The health check endpoints are configured for ALB target group health checks.

## Notes

Built this to learn about:
- Containerizing Flask apps
- Production Flask setup with Gunicorn
- AWS RDS integration
- Health check patterns for load balancers
- Environment-based configuration

## License

MIT
