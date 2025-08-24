#!/bin/bash

# stop-servers.sh - Stop all test servers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping all test servers...${NC}"

if [ -f server_pids.txt ]; then
    while IFS= read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}Stopping process ${pid}...${NC}"
            kill "$pid"
        else
            echo -e "${RED}Process ${pid} not found (already stopped?)${NC}"
        fi
    done < server_pids.txt
    
    # Clean up
    rm server_pids.txt
    echo -e "${BLUE}All servers stopped and PID file cleaned up.${NC}"
else
    echo -e "${RED}No server_pids.txt file found. Servers may not be running.${NC}"
    echo -e "${BLUE}Attempting to kill any Python servers on ports 8081-8085...${NC}"
    
    # Try to kill processes by port (alternative method)
    for port in {8081..8085}; do
        pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            echo -e "${GREEN}Killing process $pid on port $port${NC}"
            kill $pid
        fi
    done
fi

# Clean up any created docroot directories if they're empty
for i in {1..5}; do
    docroot="./docroot${i}"
    if [ -d "$docroot" ]; then
        rmdir "$docroot" 2>/dev/null && echo -e "${GREEN}Removed empty directory $docroot${NC}"
    fi
done