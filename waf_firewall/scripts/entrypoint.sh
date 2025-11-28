#!/bin/bash
set -e

echo "Starting WAF with ModSecurity..."

# Start OpenResty in daemon mode
openresty

# Give it a moment to start
sleep 2

# Check if OpenResty started successfully
if openresty -t; then
    echo "✅ OpenResty started successfully"
else
    echo "❌ OpenResty failed to start"
    exit 1
fi

# Start rule watcher in foreground
echo "Starting rule watcher..."
/watch_rules.sh



