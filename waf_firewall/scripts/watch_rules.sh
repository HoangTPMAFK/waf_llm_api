#!/bin/bash

echo "Starting ModSecurity rule watcher..."

# Function to reload nginx
reload_nginx() {
    echo "[$(date)] Detected changes in custom rules, reloading nginx..."
    openresty -t && openresty -s reload
    if [ $? -eq 0 ]; then
        echo "[$(date)] ✅ Nginx reloaded successfully"
    else
        echo "[$(date)] ❌ Nginx reload failed"
    fi
}

# Watch for changes in the custom rules file
while inotifywait -e modify,create,close_write /etc/modsec/rules/custom-rules.conf 2>/dev/null; do
    sleep 2  # Debounce multiple rapid changes
    reload_nginx
done

