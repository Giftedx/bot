# WebSocket Troubleshooting Guide

## Table of Contents
1. [Connection Issues](#connection-issues)
2. [Authentication Issues](#authentication-issues)
3. [Message Handling Issues](#message-handling-issues)
4. [Performance Issues](#performance-issues)
5. [Debugging Tools](#debugging-tools)

## Connection Issues

### Connection Failed to Establish

#### Symptoms
```
Error: WebSocket connection to 'wss://your-server.com/ws' failed
```

#### Common Causes
1. Invalid WebSocket URL
2. Network connectivity issues
3. SSL/TLS certificate problems
4. Server not running

#### Solutions
1. Verify WebSocket URL format:
   ```javascript
   // Correct format
   const ws = new WebSocket('wss://your-server.com/ws?token=your_token');
   ```

2. Check SSL certificate:
   ```bash
   openssl s_client -connect your-server.com:443 -servername your-server.com
   ```

3. Verify server status:
   ```bash
   curl -I https://your-server.com/health
   ```

### Connection Drops Frequently

#### Symptoms
```
WebSocket is closed before the connection is established
```

#### Solutions
1. Implement reconnection logic:
   ```javascript
   function connect() {
       const ws = new WebSocket(url);
       ws.onclose = () => {
           setTimeout(connect, 1000);
       };
   }
   ```

2. Check network stability:
   ```bash
   ping your-server.com
   ```

3. Monitor server resources:
   ```bash
   top -p $(pgrep -f "websocket-server")
   ```

## Authentication Issues

### Token Validation Failed

#### Symptoms
```
{"error": "Invalid token provided"}
```

#### Solutions
1. Verify token format:
   ```javascript
   // Include token in URL
   const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}`);
   ```

2. Check token expiration:
   ```python
   import jwt
   decoded = jwt.decode(token, verify=False)
   print(decoded['exp'])
   ```

3. Regenerate token if expired

### Session Authentication Failed

#### Symptoms
```
{"error": "Session authentication failed"}
```

#### Solutions
1. Verify session exists
2. Check session permissions
3. Ensure token matches session

## Message Handling Issues

### Messages Not Being Received

#### Symptoms
- Client not receiving server updates
- Missing event notifications

#### Solutions
1. Verify message handler registration:
   ```javascript
   ws.onmessage = (event) => {
       console.log('Message received:', event.data);
       // Add proper error handling
       try {
           const data = JSON.parse(event.data);
           handleMessage(data);
       } catch (error) {
           console.error('Failed to parse message:', error);
       }
   };
   ```

2. Check message format:
   ```javascript
   // Correct format
   const message = {
       type: 'event_type',
       data: {},
       timestamp: new Date().toISOString()
   };
   ```

3. Enable debug logging:
   ```javascript
   ws.onmessage = (event) => {
       console.debug('Raw message:', event.data);
       // ... rest of handler
   };
   ```

### Messages Not Being Sent

#### Symptoms
```
DOMException: Failed to execute 'send' on 'WebSocket'
```

#### Solutions
1. Check connection state:
   ```javascript
   if (ws.readyState === WebSocket.OPEN) {
       ws.send(JSON.stringify(message));
   } else {
       console.error('WebSocket is not open');
   }
   ```

2. Verify message format:
   ```javascript
   // Validate before sending
   function validateMessage(message) {
       if (!message.type || !message.data) {
           throw new Error('Invalid message format');
       }
   }
   ```

## Performance Issues

### High Latency

#### Symptoms
- Delayed message delivery
- Increased response times

#### Solutions
1. Monitor message timing:
   ```javascript
   const start = Date.now();
   ws.send(message);
   ws.onmessage = () => {
       const latency = Date.now() - start;
       console.log(`Message latency: ${latency}ms`);
   };
   ```

2. Implement heartbeat monitoring:
   ```javascript
   function startHeartbeat() {
       setInterval(() => {
           if (ws.readyState === WebSocket.OPEN) {
               const start = Date.now();
               ws.send(JSON.stringify({type: 'heartbeat'}));
           }
       }, 30000);
   }
   ```

### Memory Leaks

#### Symptoms
- Increasing memory usage
- Degraded performance over time

#### Solutions
1. Clean up event listeners:
   ```javascript
   class WebSocketClient {
       disconnect() {
           if (this.ws) {
               this.ws.onmessage = null;
               this.ws.onclose = null;
               this.ws.onerror = null;
               this.ws.close();
               this.ws = null;
           }
       }
   }
   ```

2. Monitor memory usage:
   ```javascript
   // Chrome DevTools
   performance.memory
   ```

## Debugging Tools

### Browser DevTools

1. Open WebSocket tab in Network panel
2. Monitor messages in real-time
3. Check for errors in Console

### Server-Side Logging

1. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Log WebSocket events:
   ```python
   async def on_message(websocket, message):
       logging.debug(f"Received message: {message}")
   ```

### Network Analysis

1. Use Wireshark for packet analysis:
   ```bash
   wireshark -i any -f "tcp port 443"
   ```

2. Monitor network traffic:
   ```bash
   tcpdump -i any port 443
   ```

## Best Practices

### Error Handling
```javascript
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // Implement appropriate error recovery
};
```

### Message Validation
```javascript
function validateMessage(message) {
    const requiredFields = ['type', 'data', 'timestamp'];
    return requiredFields.every(field => message.hasOwnProperty(field));
}
```

### Connection Management
```javascript
class WebSocketManager {
    constructor(url, options = {}) {
        this.url = url;
        this.options = options;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    }

    connect() {
        this.ws = new WebSocket(this.url);
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.ws.onclose = this.handleClose.bind(this);
        this.ws.onerror = this.handleError.bind(this);
        this.ws.onmessage = this.handleMessage.bind(this);
    }

    handleClose() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), this.getReconnectDelay());
        }
    }

    getReconnectDelay() {
        return Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    }
}
```

## Common Error Codes

### 1000 - Normal Closure
- Expected closure
- Clean disconnection

### 1001 - Going Away
- Server is shutting down
- Client should reconnect later

### 1006 - Abnormal Closure
- Connection dropped unexpectedly
- Implement reconnection logic

### 1011 - Internal Error
- Server encountered an error
- Log error details for debugging

## Support Resources

1. Check WebSocket server logs
2. Review client-side console
3. Analyze network traffic
4. Contact support team

## Prevention

### Regular Testing
1. Implement health checks
2. Monitor connection stability
3. Test reconnection logic
4. Verify message handling

### Performance Monitoring
1. Track message latency
2. Monitor memory usage
3. Log error rates
4. Analyze connection patterns 