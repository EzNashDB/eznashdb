FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    postgresql-client \
    cron \
    curl \
    unzip \
    nano \
    && curl https://rclone.org/install.sh | bash \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /django

# Copy Poetry files from parent directory
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi

# Copy the entire Django project
COPY . ./

# Copy worker-specific files
COPY worker-service/crontab /etc/cron.d/worker-cron
RUN chmod 0644 /etc/cron.d/worker-cron

# Create log file
RUN touch /var/log/cron.log

# Run cron in foreground
CMD printenv > /etc/environment && \
    mkdir -p /root/.config/rclone && \
    echo "$RCLONE_CONFIG_CONTENT" > /root/.config/rclone/rclone.conf && \
    crontab /etc/cron.d/worker-cron && \
    cron && \
    echo "Cron started. Current crontab:" && \
    crontab -l && \
    tail -f /var/log/cron.log
