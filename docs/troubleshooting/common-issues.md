# Common Issues and Troubleshooting

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Authentication Issues](#authentication-issues)
3. [Discord Integration Issues](#discord-integration-issues)
4. [Plex Integration Issues](#plex-integration-issues)
5. [Playback Issues](#playback-issues)
6. [Performance Issues](#performance-issues)
7. [API Issues](#api-issues)

## Installation Issues

### Dependencies Installation Fails
```
ERROR: Could not install packages due to an OSError
```

**Solution:**
1. Ensure you have Python 3.8+ installed
2. Try upgrading pip: `python -m pip install --upgrade pip`
3. Install build tools:
   - Windows: `pip install wheel`
   - Linux: `sudo apt-get install python3-dev build-essential`

### Redis Connection Error
```
Error: Error connecting to Redis on localhost:6379
```

**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check Redis configuration in `.env`
3. Ensure Redis port is not blocked by firewall

## Authentication Issues

### Invalid Discord Token
```
discord.errors.LoginFailure: Improper token has been passed
```

**Solution:**
1. Verify token in `.env` file
2. Regenerate token in Discord Developer Portal
3. Ensure bot has required permissions

### JWT Token Issues
```
{"error": "Token has expired"}
```

**Solution:**
1. Request new token through authentication endpoint
2. Check system time synchronization
3. Verify token expiration settings

## Discord Integration Issues

### Bot Not Responding to Commands
1. Check if bot is online in Discord
2. Verify command prefix
3. Check bot permissions in server
4. Review bot logs for errors

### Voice Channel Connection Failed
```
Error: Cannot connect to voice channel
```

**Solution:**
1. Verify bot has voice permissions
2. Check if bot is already in another channel
3. Ensure voice channel is not full
4. Check network connectivity

## Plex Integration Issues

### Plex Server Connection Failed
```
ERROR: Unable to connect to Plex server at https://your-server:32400
```

**Solution:**
1. Verify Plex server URL in `.env`
2. Check Plex token validity
3. Ensure Plex server is online
4. Check network/firewall settings

### Media Not Found
```
ERROR: Media item not found in Plex library
```

**Solution:**
1. Refresh Plex library
2. Verify media file exists
3. Check file permissions
4. Ensure media is properly indexed

## Playback Issues

### Streaming Quality Problems
1. Check internet connection speed
2. Verify stream quality settings
3. Monitor CPU/memory usage
4. Check Discord voice region

### Audio Sync Issues
1. Adjust buffer size settings
2. Check for network latency
3. Verify audio codec support
4. Monitor system resources

### Playback Controls Not Working
1. Check WebSocket connection
2. Verify session state
3. Review command permissions
4. Check client-side event handlers

## Performance Issues

### High CPU Usage
1. Monitor resource usage:
   ```bash
   top -p $(pgrep -f "discord-plex-player")
   ```
2. Check for memory leaks
3. Review logging level
4. Optimize media transcoding settings

### Slow Response Times
1. Enable performance monitoring
2. Check Redis cache usage
3. Monitor database queries
4. Review network latency

### Memory Leaks
1. Use memory profiler:
   ```python
   from memory_profiler import profile
   ```
2. Monitor memory usage over time
3. Check for unclosed connections
4. Review object lifecycle

## API Issues

### Rate Limiting
```
{"error": "Too many requests"}
```

**Solution:**
1. Implement request throttling
2. Cache frequently accessed data
3. Review API usage patterns
4. Increase rate limits if needed

### Endpoint Timeouts
```
Error: Request timed out after 30000ms
```

**Solution:**
1. Check server load
2. Review timeout settings
3. Optimize endpoint performance
4. Monitor network connectivity

## Logging and Debugging

### Enable Debug Logging
1. Set `LOG_LEVEL=DEBUG` in `.env`
2. Check logs in specified log file
3. Use logging format:
   ```python
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

### Common Log Messages

#### WebSocket Connection Issues
```
WARNING: WebSocket connection closed unexpectedly
```
- Check network stability
- Review connection lifecycle
- Monitor heartbeat messages

#### Discord API Errors
```
ERROR: Discord API returned 403 Forbidden
```
- Verify bot permissions
- Check rate limiting
- Review API documentation

#### Plex API Issues
```
ERROR: Failed to authenticate with Plex server
```
- Verify Plex credentials
- Check server status
- Review API access settings

## Quick Fixes

### Reset Application State
1. Clear Redis cache:
   ```bash
   redis-cli FLUSHALL
   ```
2. Restart bot service
3. Reconnect to voice channels
4. Verify configuration

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Rebuild Cache
1. Clear existing cache
2. Warm up cache with common requests
3. Monitor cache hit rates

## Getting Help

### Gathering Information
1. Application version
2. System information
3. Error logs
4. Steps to reproduce

### Reporting Issues
1. Check existing issues
2. Provide detailed description
3. Include error logs
4. Share reproduction steps

### Community Support
1. Join Discord server
2. Check documentation
3. Search GitHub issues
4. Contact maintainers

## Prevention

### Regular Maintenance
1. Update dependencies
2. Monitor logs
3. Review performance metrics
4. Backup configuration

### Best Practices
1. Follow rate limits
2. Implement error handling
3. Use caching effectively
4. Monitor resource usage

### Security
1. Keep tokens secure
2. Update regularly
3. Monitor access logs
4. Review permissions 