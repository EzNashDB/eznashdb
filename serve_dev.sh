#!/bin/bash

# Function to install unbuffer if not already installed
install_unbuffer() {
    if ! command -v unbuffer > /dev/null; then
        echo "Installing unbuffer..."
        sudo apt-get install expect   # Use appropriate package manager for your system
    fi
}

# Install unbuffer if needed
install_unbuffer

# Function to clean up and terminate both commands
cleanup() {
    echo "Stopping both commands..."
    pkill -P $$  # Kill all child processes of the script
    exit
}

# Set up a trap to catch the Ctrl+C signal (SIGINT) and call the cleanup function
trap cleanup INT

# Run the Django development server in the foreground (interactive)

# Run the npm watch command in the background
unbuffer npm run watch 2>&1 | while IFS= read -r line; do
    echo -e "$line"
done &
pid=$!

poetry run python manage.py runserver 0.0.0.0:8000

# Wait for the npm watch command to complete
wait $pid

echo "npm watch command has completed."
