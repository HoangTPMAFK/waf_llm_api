FROM openresty/openresty:1.21.4.3-0-jammy

# Install ModSecurity and dependencies
RUN apt-get update && apt-get install -y \
    libmodsecurity3 \
    libmodsecurity-dev \
    modsecurity-crs \
    git \
    wget \
    build-essential \
    libpcre3-dev \
    zlib1g-dev \
    libssl-dev \
    inotify-tools \
    && rm -rf /var/lib/apt/lists/*

# lua-resty-http is included in OpenResty by default, no need to install

# Download and compile ModSecurity-nginx connector for OpenResty
# OpenResty 1.21.4.3 is based on nginx 1.21.4
WORKDIR /tmp
RUN wget http://nginx.org/download/nginx-1.21.4.tar.gz && \
    tar -xzvf nginx-1.21.4.tar.gz && \
    git clone --depth 1 https://github.com/SpiderLabs/ModSecurity-nginx.git && \
    cd nginx-1.21.4 && \
    ./configure --with-compat --add-dynamic-module=../ModSecurity-nginx && \
    make modules && \
    mkdir -p /usr/local/openresty/nginx/modules && \
    cp objs/ngx_http_modsecurity_module.so /usr/local/openresty/nginx/modules/

# Copy configuration files
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY modsecurity.conf /etc/modsecurity/modsecurity.conf
COPY modsec/main.conf /etc/modsecurity/main.conf

# Copy Lua scripts
RUN mkdir -p /usr/local/openresty/nginx/lua
COPY lua/ /usr/local/openresty/nginx/lua/

# Download unicode.map file
RUN wget -O /etc/modsecurity/unicode.map \
    https://raw.githubusercontent.com/SpiderLabs/ModSecurity/v3/master/unicode.map || \
    touch /etc/modsecurity/unicode.map

# Create directories for custom rules
RUN mkdir -p /etc/modsec/rules && \
    touch /etc/modsec/rules/custom-rules.conf

# Copy OWASP Core Rule Set
RUN cp /etc/modsecurity/crs-setup.conf.example /etc/modsecurity/crs-setup.conf || true

# Copy watch script
COPY scripts/watch_rules.sh /watch_rules.sh
RUN chmod +x /watch_rules.sh

EXPOSE 80

# Start OpenResty and rule watcher
CMD openresty -g "daemon off;" & /watch_rules.sh

