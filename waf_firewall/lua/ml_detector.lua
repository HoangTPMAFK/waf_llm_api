-- Lua script to forward requests to ML Detector using OpenResty cosocket
local cjson = require "cjson.safe"

-- Function to send request data to ML detector
local function send_to_ml_detector()
    -- Get request data
    local request_method = ngx.var.request_method
    local request_uri = ngx.var.request_uri
    local remote_addr = ngx.var.remote_addr
    
    -- Read request body if present
    ngx.req.read_body()
    local request_body = ngx.req.get_body_data() or ""
    
    -- Get request headers
    local headers = ngx.req.get_headers()
    local headers_str = ""
    for k, v in pairs(headers) do
        headers_str = headers_str .. k .. ": " .. tostring(v) .. "; "
    end
    
    -- Get query arguments
    local args = ngx.req.get_uri_args()
    local args_str = ""
    for k, v in pairs(args) do
        args_str = args_str .. k .. "=" .. tostring(v) .. "&"
    end
    
    -- Build the full request string for analysis
    local full_request = request_method .. " " .. request_uri
    if args_str ~= "" then
        full_request = full_request .. "?" .. args_str
    end
    if request_body ~= "" then
        full_request = full_request .. " Body: " .. request_body
    end
    
    -- Prepare JSON payload for ML detector
    local payload = {
        request_data = full_request,
        client_ip = remote_addr,
        method = request_method,
        uri = request_uri
    }
    
    local json_payload = cjson.encode(payload)
    if not json_payload then
        ngx.log(ngx.ERR, "Failed to encode JSON")
        return
    end
    
    -- Create TCP socket connection to ML detector
    local sock = ngx.socket.tcp()
    sock:settimeout(1000)  -- 1 second timeout
    
    local ok, err = sock:connect("ml_detector", 5000)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to ML detector: ", err)
        return
    end
    
    -- Build HTTP request
    local http_request = string.format(
        "POST /api/detect HTTP/1.1\r\n" ..
        "Host: ml_detector:5000\r\n" ..
        "Content-Type: application/json\r\n" ..
        "Content-Length: %d\r\n" ..
        "Connection: close\r\n" ..
        "\r\n" ..
        "%s",
        #json_payload, json_payload
    )
    
    -- Send request
    local bytes, err = sock:send(http_request)
    if not bytes then
        ngx.log(ngx.ERR, "Failed to send to ML detector: ", err)
        sock:close()
        return
    end
    
    -- Read response (non-blocking)
    local response, err = sock:receive("*a")
    sock:close()
    
    if response then
        -- Parse response to check if malicious
        if response:match('"is_safe"%s*:%s*false') then
            ngx.log(ngx.WARN, "🚨 ML Detector flagged request as MALICIOUS: ", full_request:sub(1, 100))
        else
            ngx.log(ngx.INFO, "✅ ML Detector: request is safe")
        end
    end
end

-- Execute the function
local ok, err = pcall(send_to_ml_detector)
if not ok then
    ngx.log(ngx.ERR, "Error in ML detector integration: ", err)
end
