# Connection Refused Issue - Development Environment

**Date:** July 21, 2025  
**Project:** SY Media Downloader  
**Issue:** ERR_CONNECTION_REFUSED when accessing localhost:3000

## Issue Summary

The web application experienced a "This site can't be reached - localhost refused to connect" error when attempting to access the frontend through the browser preview.

## Technical Analysis

### Root Cause
The React development server running on port 3000 had stopped or crashed, while the FastAPI backend on port 8000 remained active. This created a scenario where:

1. The browser preview proxy attempted to connect to `http://localhost:3000`
2. No process was listening on port 3000
3. The connection was refused by the operating system
4. The browser displayed `ERR_CONNECTION_REFUSED`

### Architecture Context
The application uses a two-tier architecture:
- **Frontend**: React development server (port 3000)
- **Backend**: FastAPI with uvicorn (port 8000)

Both services must be running simultaneously for the application to function correctly.

### Technical Details
- **Error Code**: ERR_CONNECTION_REFUSED
- **Affected Port**: 3000 (React dev server)
- **Working Port**: 8000 (FastAPI backend)
- **Verification Command**: `lsof -i :3000` returned no results
- **Resolution**: Restart React dev server with `npm start`

## Non-Technical Explanation

### What Happened
Think of your web application like a restaurant with two parts:
- **Kitchen (Backend)**: Prepares the food (processes download requests)
- **Dining Room (Frontend)**: Where customers sit and place orders (the website interface)

The kitchen was still running and ready to cook, but the dining room had closed. When customers (users) tried to enter the restaurant, they found the doors locked and couldn't get in.

### Why It Happened
Development servers can stop running for various reasons:
- Computer went to sleep or hibernated
- Process was accidentally terminated
- System resources were exhausted
- Terminal window was closed
- Development server crashed due to code errors

## Prevention Strategies

### For Developers

#### 1. Process Monitoring
```bash
# Check if both services are running
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Alternative using ps
ps aux | grep "react-scripts\|uvicorn"
```

#### 2. Automated Startup Scripts
Create a startup script to launch both services:

```bash
#!/bin/bash
# start-dev-servers.sh

echo "Starting Media Downloader development environment..."

# Start backend
cd webapp/backend
uvicorn main:app --reload &
BACKEND_PID=$!

# Start frontend
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Both servers started. Press Ctrl+C to stop both."

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
```

#### 3. Docker Compose Solution
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build: ./webapp/frontend
    ports:
      - "3000:3000"
    volumes:
      - ./webapp/frontend:/app
    depends_on:
      - backend
      
  backend:
    build: ./webapp/backend
    ports:
      - "8000:8000"
    volumes:
      - ./webapp/backend:/app
```

#### 4. Package.json Scripts
Add convenience scripts to `package.json`:

```json
{
  "scripts": {
    "dev": "concurrently \"npm run backend\" \"npm run frontend\"",
    "backend": "cd ../backend && uvicorn main:app --reload",
    "frontend": "react-scripts start",
    "check-ports": "lsof -i :3000 && lsof -i :8000"
  }
}
```

#### 5. Health Check Endpoints
Implement health check endpoints in both services:

**Frontend** (React):
```javascript
// Add to App.js
useEffect(() => {
  const healthCheck = async () => {
    try {
      await fetch('http://localhost:8000/health');
      setBackendStatus('connected');
    } catch {
      setBackendStatus('disconnected');
    }
  };
  healthCheck();
}, []);
```

**Backend** (FastAPI):
```python
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

### For Non-Technical Users

#### 1. Visual Indicators
- Add status indicators in the UI showing connection status
- Display clear error messages when services are down
- Provide "retry connection" buttons

#### 2. Documentation
- Create simple startup guides with screenshots
- Document common error messages and solutions
- Provide troubleshooting checklists

#### 3. Automated Recovery
- Implement automatic retry mechanisms
- Add service restart buttons in the UI
- Create desktop shortcuts for starting services

## Troubleshooting Checklist

### When ERR_CONNECTION_REFUSED Occurs:

1. **Check Process Status**
   ```bash
   lsof -i :3000
   lsof -i :8000
   ```

2. **Restart Frontend Service**
   ```bash
   cd webapp/frontend
   npm start
   ```

3. **Restart Backend Service**
   ```bash
   cd webapp/backend
   uvicorn main:app --reload
   ```

4. **Verify Network Connectivity**
   ```bash
   curl http://localhost:3000
   curl http://localhost:8000/health
   ```

5. **Check for Port Conflicts**
   ```bash
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000
   ```

## Lessons Learned

1. **Always verify both services are running** before testing
2. **Implement health checks** for better monitoring
3. **Use process managers** in production environments
4. **Document startup procedures** for team members
5. **Consider containerization** for consistent environments

## Future Improvements

1. Add automatic service discovery
2. Implement graceful error handling
3. Create monitoring dashboards
4. Add automated testing for service connectivity
5. Implement circuit breaker patterns

---

**Resolution Time:** ~5 minutes  
**Impact:** Development workflow interruption  
**Severity:** Low (development environment only)  
**Status:** Resolved
