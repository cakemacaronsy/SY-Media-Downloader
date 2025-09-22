# 🚀 SY Media Downloader - Deployment Guide

## Overview
This guide covers multiple deployment options for the SY Media Downloader application.

## Architecture Options

### Option 1: Vercel + Railway (Recommended) ⭐
- **Frontend**: Vercel (free tier available)
- **Backend**: Railway ($5/month with free trial)
- **Pros**: Easy setup, great performance, automatic deployments
- **Cons**: Railway requires payment after trial

### Option 2: Vercel + Render
- **Frontend**: Vercel (free tier)
- **Backend**: Render (free tier with limitations)
- **Pros**: Completely free option available
- **Cons**: Render free tier has slow cold starts

### Option 3: Full Render Deployment
- **Frontend & Backend**: Both on Render
- **Pros**: Single platform, easy management
- **Cons**: Limited free tier resources

### Option 4: Vercel + Supabase Edge Functions
- **Frontend**: Vercel
- **Backend**: Supabase Edge Functions
- **Pros**: Serverless, scalable
- **Cons**: Requires adaptation for yt-dlp functionality

---

## 📱 Frontend Deployment (Vercel)

### Step 1: Prepare the Frontend
1. Apply all the configuration files created above
2. Update the API URL in `.env.production`

### Step 2: Deploy to Vercel

#### Via GitHub (Recommended):
1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "Import Project"
4. Select your GitHub repository
5. Configure:
   - Framework Preset: `Create React App`
   - Root Directory: `webapp/frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`
6. Add environment variable:
   - `REACT_APP_API_URL`: Your backend URL (add after backend deployment)
7. Click "Deploy"

#### Via Vercel CLI:
```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend
cd webapp/frontend

# Deploy
vercel

# Follow prompts and set:
# - Project Path: ./
# - Framework: Create React App
```

---

## 🖥️ Backend Deployment

### Option A: Railway Deployment (Recommended)

1. **Sign up** at [railway.app](https://railway.app)

2. **Create New Project**:
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login
   railway login
   
   # Initialize project in backend directory
   cd webapp/backend
   railway init
   ```

3. **Configure Environment Variables** in Railway Dashboard:
   - `ALLOWED_ORIGINS`: Your Vercel frontend URL (e.g., `https://your-app.vercel.app`)
   - `PORT`: (Railway sets this automatically)
   - `PYTHON_VERSION`: `3.11`

4. **Deploy**:
   ```bash
   railway up
   ```

5. **Get your deployment URL** from Railway dashboard

### Option B: Render Deployment

1. **Sign up** at [render.com](https://render.com)

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Choose "Python" environment
   - Set Build Command: `cd webapp/backend && pip install -r requirements.txt`
   - Set Start Command: `cd webapp/backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Configure Environment Variables**:
   - `ALLOWED_ORIGINS`: Your frontend URL
   - `PYTHON_VERSION`: `3.11.0`

4. **Deploy** (automatic from GitHub)

### Option C: Supabase Edge Functions

1. **Install Supabase CLI**:
   ```bash
   brew install supabase/tap/supabase
   ```

2. **Initialize Supabase**:
   ```bash
   supabase init
   ```

3. **Deploy Functions**:
   ```bash
   supabase functions deploy download
   ```

4. **Note**: This option requires additional setup for yt-dlp functionality

---

## 🔧 Post-Deployment Configuration

### 1. Update Frontend Environment
After deploying the backend, update your frontend:

1. Go to Vercel Dashboard
2. Settings → Environment Variables
3. Update `REACT_APP_API_URL` with your backend URL
4. Redeploy frontend

### 2. Configure CORS
Ensure your backend CORS settings allow your frontend domain:

```python
# In main.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
```

### 3. Test the Deployment
1. Visit your frontend URL
2. Try downloading a video
3. Check browser console for any CORS errors
4. Verify API endpoints at `https://your-backend-url/docs`

---

## 🐳 Alternative: Docker Deployment

### Create Dockerfile for Backend:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY webapp/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp/backend .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deploy to Cloud Providers:
- **Google Cloud Run**
- **AWS App Runner**
- **Azure Container Instances**
- **DigitalOcean App Platform**

---

## 🔒 Security Considerations

1. **API Rate Limiting**: Add rate limiting to prevent abuse
2. **File Size Limits**: Implement maximum download size
3. **Authentication**: Consider adding user authentication
4. **HTTPS**: Always use HTTPS in production
5. **Environment Variables**: Never commit sensitive data

---

## 💰 Cost Estimates

| Platform | Frontend | Backend | Total Monthly |
|----------|----------|---------|---------------|
| Vercel + Railway | Free | $5 | $5 |
| Vercel + Render | Free | Free* | Free |
| Full Render | Free* | Free* | Free |
| Vercel + Supabase | Free | Free** | Free |

*With limitations (slow cold starts, limited compute)
**Up to 500K invocations/month

---

## 🚨 Troubleshooting

### CORS Errors
- Verify `ALLOWED_ORIGINS` environment variable
- Check frontend is using correct API URL
- Ensure backend CORS middleware is configured

### Download Failures
- Check yt-dlp is installed in production
- Verify ffmpeg is available (for some formats)
- Check disk space on server

### Slow Performance
- Consider upgrading to paid tiers
- Implement caching
- Use CDN for static files

---

## 📞 Support

For deployment issues:
1. Check the logs in your hosting platform
2. Verify all environment variables are set
3. Test API endpoints directly
4. Check browser console for errors

---

## 🎉 Success!

Once deployed, your app will be available at:
- Frontend: `https://your-app.vercel.app`
- Backend API: `https://your-backend.railway.app`
- API Docs: `https://your-backend.railway.app/docs`

Share your media downloader with the world! 🌍
