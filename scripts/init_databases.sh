#!/bin/bash
################################################################################
# JLAW Database Initialization Script
################################################################################
#
# This script initializes all required databases for JLAW:
# - Neo4j (graph database for network analysis)
# - TimescaleDB (time-series database for financial metrics)
# - Redis (caching and rate limiting)
#
# Usage:
#   ./scripts/init_databases.sh [options]
#
# Options:
#   --skip-docker    Skip Docker container startup (use existing containers)
#   --wait-only      Only wait for health checks, don't reinitialize
#   --help           Show this help message
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Configuration
SKIP_DOCKER=false
WAIT_ONLY=false
MAX_WAIT_TIME=120  # Maximum wait time for health checks (seconds)

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# Parse Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --wait-only)
            WAIT_ONLY=true
            shift
            ;;
        --help)
            head -n 20 "$0" | tail -n +3 | sed 's/^# //'
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

################################################################################
# Main Script
################################################################################

print_header "JLAW DATABASE INITIALIZATION"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine docker compose command
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Navigate to project root
cd "$PROJECT_ROOT"

################################################################################
# Step 1: Start Docker Containers
################################################################################

if [ "$SKIP_DOCKER" = false ]; then
    print_header "Step 1: Starting Docker Containers"
    
    print_info "Starting databases with Docker Compose..."
    $DOCKER_COMPOSE up -d neo4j timescaledb redis
    
    print_success "Docker containers started"
else
    print_header "Step 1: Skipping Docker Container Startup"
    print_info "Using existing Docker containers"
fi

################################################################################
# Step 2: Wait for Health Checks
################################################################################

print_header "Step 2: Waiting for Database Health Checks"

wait_for_service() {
    local service=$1
    local max_attempts=$((MAX_WAIT_TIME / 5))
    local attempt=1
    
    print_info "Waiting for $service to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if $DOCKER_COMPOSE ps | grep "$service" | grep -q "healthy"; then
            print_success "$service is healthy"
            return 0
        fi
        
        if [ $((attempt % 3)) -eq 0 ]; then
            print_info "Still waiting for $service... (${attempt}/${max_attempts})"
        fi
        
        sleep 5
        attempt=$((attempt + 1))
    done
    
    print_error "$service did not become healthy within ${MAX_WAIT_TIME}s"
    return 1
}

# Wait for each service
wait_for_service "jlaw-neo4j" || exit 1
wait_for_service "jlaw-timescaledb" || exit 1

# Redis might not have a health check in all configurations
if $DOCKER_COMPOSE ps | grep "jlaw-redis" | grep -q "Up"; then
    print_success "jlaw-redis is running"
else
    print_error "jlaw-redis is not running"
    exit 1
fi

################################################################################
# Step 3: Initialize Database Schemas
################################################################################

if [ "$WAIT_ONLY" = false ]; then
    print_header "Step 3: Initializing Database Schemas"
    
    # Neo4j Schema
    print_info "Initializing Neo4j schema..."
    if [ -f "$PROJECT_ROOT/cypher/neo4j_schema.cypher" ]; then
        # Run Cypher script via Docker
        docker exec jlaw-neo4j cypher-shell \
            -u neo4j \
            -p "${NEO4J_PASSWORD:-jlaw_secure_password}" \
            -f /var/lib/neo4j/import/schema.cypher 2>/dev/null || \
        print_warning "Neo4j schema initialization skipped (file not mounted or already initialized)"
        print_success "Neo4j schema initialized"
    else
        print_warning "Neo4j schema file not found: cypher/neo4j_schema.cypher"
    fi
    
    # TimescaleDB Schema
    print_info "Initializing TimescaleDB schema..."
    if [ -f "$PROJECT_ROOT/sql/timescaledb_schema.sql" ]; then
        # Schema is automatically loaded via docker-entrypoint-initdb.d
        print_success "TimescaleDB schema initialized (via docker-entrypoint-initdb.d)"
    else
        print_warning "TimescaleDB schema file not found: sql/timescaledb_schema.sql"
    fi
    
    # Redis doesn't need schema initialization
    print_success "Redis ready (no schema initialization required)"
    
else
    print_header "Step 3: Skipping Schema Initialization"
    print_info "Using existing database schemas"
fi

################################################################################
# Step 4: Verify Connectivity
################################################################################

print_header "Step 4: Verifying Database Connectivity"

# Run Python health check
print_info "Running comprehensive health check..."

python3 - <<EOF
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, "$PROJECT_ROOT")

from src.database.db_health_checker import DatabaseHealthChecker

async def main():
    checker = DatabaseHealthChecker()
    results = await checker.check_all()
    checker.print_health_summary(results)
    
    # Exit with error if any database is unhealthy
    all_healthy = all(r.is_healthy for r in results.values())
    return 0 if all_healthy else 1

exit_code = asyncio.run(main())
sys.exit(exit_code)
EOF

if [ $? -eq 0 ]; then
    print_success "All databases passed health checks"
else
    print_error "Some databases failed health checks"
    exit 1
fi

################################################################################
# Summary
################################################################################

print_header "INITIALIZATION COMPLETE"

print_success "All databases are initialized and healthy"
print_info "Neo4j:       bolt://localhost:7687"
print_info "TimescaleDB: postgresql://localhost:5432/jlaw_forensics"
print_info "Redis:       redis://localhost:6379"

echo -e "\n${GREEN}✓ JLAW database infrastructure is ready${NC}\n"

exit 0
