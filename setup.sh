#!/bin/bash

# Fraud Monitor Setup Script
# This script helps set up the fraud monitoring system

set -e

echo "🔧 Setting up Fraud Monitor..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp env.example .env
    
    # Generate secure passwords and keys
    ./scripts/generate_keys.py
    
    print_warning "Please update the following in your .env file:"
    print_warning "- TELEGRAM_BOT_TOKEN: Get this from @BotFather on Telegram"
    print_warning "- TELEGRAM_GROUP_IDS: Add your group IDs (comma-separated)"
    # print_warning "- WEBHOOK_URL: Add your webhook endpoint for alerts (optional)"
    
    echo ""
    print_status "Generated secure passwords and keys in .env file"
else
    print_status ".env file already exists"
fi

# Create logs directory
mkdir -p logs
print_status "Created logs directory"

# Set proper permissions for logs
chmod 755 logs

print_status "Set directory permissions"

# Build Docker images
print_status "Building Docker images..."
docker-compose build

print_status "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with your Telegram bot token and group IDs"
echo "2. Run 'docker-compose up -d' to start the services"
echo "3. Check logs with 'docker-compose logs -f app'"
echo "4. Access monitoring at http://localhost:8000/health"
echo ""
echo "For more information, see the README.md file."

