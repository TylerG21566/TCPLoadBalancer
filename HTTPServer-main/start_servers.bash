#!/bin/bash

# start-servers.sh - Start 5 test servers for load balancer testing

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PYTHON_SCRIPT="main.py"  # Change this to your actual script name
BASE_PORT=8081
HOST="localhost"
BASE_DOCROOT="./docroot"

echo -e "${BLUE}Starting 5 test servers for load balancer testing...${NC}"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}Error: Python script '$PYTHON_SCRIPT' not found!${NC}"
    echo -e "${YELLOW}Please make sure the script exists in the current directory.${NC}"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found!${NC}"
    echo -e "${YELLOW}Please install Python 3 or use 'python' instead of 'python3'${NC}"
    exit 1
fi

# Function to start a server
start_server() {
    local server_num=$1
    local port=$((BASE_PORT + server_num - 1))
    local docroot="${BASE_DOCROOT}${server_num}"
    
    echo -e "${GREEN}Starting Server ${server_num} on port ${port} with docroot ${docroot}...${NC}"
    
    # Start server and capture output for debugging
    python3 "$PYTHON_SCRIPT" --host="$HOST" --port="$port" --docroot="$docroot" > "server${server_num}.log" 2>&1 &
    
    local pid=$!
    echo $pid >> server_pids.txt
    
    # Check if the process is still running after a moment
    sleep 1
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✓ Server ${server_num} started successfully (PID: ${pid})${NC}"
    else
        echo -e "${RED}✗ Server ${server_num} failed to start! Check server${server_num}.log${NC}"
        # Show the error
        echo -e "${YELLOW}Error output:${NC}"
        cat "server${server_num}.log"
    fi
}

# Clean up any existing PID file
rm -f server_pids.txt

# Kill any existing processes on our target ports
echo -e "${YELLOW}Checking for existing processes on ports 8081-8085...${NC}"
for port in {8081..8085}; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing existing process $pid on port $port${NC}"
        kill $pid 2>/dev/null
        sleep 0.5
    fi
done

# Start all 5 servers
for i in {1..5}; do
    start_server $i
done

echo -e "${BLUE}All servers started!${NC}"
echo -e "${BLUE}Servers running on ports: 8081, 8082, 8083, 8084, 8085${NC}"
echo -e "${BLUE}PIDs saved to server_pids.txt${NC}"
echo ""
echo -e "${BLUE}To stop all servers, run:${NC}"
echo -e "${GREEN}./stop-servers.sh${NC}"
echo -e "${BLUE}Or manually:${NC}"
echo -e "${GREEN}kill \$(cat server_pids.txt)${NC}"
echo ""
echo -e "${BLUE}Test the servers:${NC}"
for i in {1..5}; do
    port=$((BASE_PORT + i - 1))
    echo -e "${GREEN}curl http://localhost:${port}/${NC}"
done