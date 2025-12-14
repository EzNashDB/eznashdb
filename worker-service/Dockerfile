FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    postgresql-client \
    cron \
    curl \
    unzip \
    && curl https://rclone.org/install.sh | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /django

# Copy Poetry files from parent directory
COPY ../pyproject.toml ../poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy the entire Django project
COPY ../ ./

# Copy worker-specific files
COPY crontab /etc/cron.d/worker-cron
RUN chmod 0644 /etc/cron.d/worker-cron && \
    crontab /etc/cron.d/worker-cron

# Create log file
RUN touch /var/log/cron.log

# Run cron in foreground
CMD cron && tail -f /var/log/cron.log
```

## 2. `worker-service/crontab`
```
# Run daily backup at 2 AM
0 2 * * * cd /django && python manage.py backup_database >> /var/log/cron.log 2>&1

# Add more cron jobs as needed
