# 🚀 Deployment Guide for Video Extractor API

## Quick Deploy to Render

### Option 1: One-Click Deploy (Recommended)

1. **Fork this repository** to your GitHub account
2. **Click the deploy button** (add this to your repo):
   
   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

3. **Configure deployment:**
   - Service Name: `video-extractor-api`
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app --timeout 300 --workers 2`

### Option 2: Manual Deployment

1. **Create Render Account:** Go to [render.com](https://render.com) and sign up

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Or upload files manually

3. **Configure Service:**
   ```
   Name: video-extractor-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT app:app --timeout 300 --workers 2
   ```

4. **Environment Variables (Optional):**
   ```
   PYTHON_VERSION=3.11.0
   ```

5. **Deploy:** Click "Create Web Service"

## Testing Before Deployment

### Local Testing

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally:**
   ```bash
   python app.py
   ```

3. **Test the API:**
   ```bash
   python test_api.py
   ```

4. **Open web interface:**
   ```
   http://localhost:5000
   ```

### Test Endpoints

```bash
# Health check
curl https://your-app.onrender.com/health

# Extract sources
curl -X POST https://your-app.onrender.com/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Start download
curl -X POST https://your-app.onrender.com/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "best"}'
```

## Post-Deployment Setup

### 1. Verify Deployment

After deployment, your API will be available at:
```
https://your-app-name.onrender.com
```

Test it with:
```bash
python test_api.py https://your-app-name.onrender.com
```

### 2. Custom Domain (Optional)

1. Go to your service settings in Render
2. Add custom domain
3. Configure DNS records

### 3. Environment Variables

Add these in Render dashboard if needed:
- `PYTHON_VERSION=3.11.0`
- Any custom configuration

## Usage Examples

### Web Interface

Visit your deployed URL to use the web interface:
```
https://your-app-name.onrender.com
```

### API Integration

```python
import requests

API_BASE = "https://your-app-name.onrender.com"

# Extract video sources
response = requests.post(f"{API_BASE}/extract", 
                        json={"url": "https://example.com/video"})
sources = response.json()

# Start download
response = requests.post(f"{API_BASE}/download",
                        json={"url": "https://example.com/video", "quality": "best"})
download_info = response.json()
download_id = download_info["download_id"]

# Check progress
status = requests.get(f"{API_BASE}/status/{download_id}").json()

# Download file when ready
if status["status"] == "completed":
    file_data = requests.get(f"{API_BASE}/download/{download_id}")
    with open("video.mp4", "wb") as f:
        f.write(file_data.content)
```

### JavaScript/Frontend Integration

```javascript
// Extract sources
const extractResponse = await fetch('https://your-app-name.onrender.com/extract', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: 'https://example.com/video'})
});
const sources = await extractResponse.json();

// Start download
const downloadResponse = await fetch('https://your-app-name.onrender.com/download', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: 'https://example.com/video', quality: 'best'})
});
const downloadInfo = await downloadResponse.json();

// Poll for status
const checkStatus = async () => {
    const statusResponse = await fetch(`https://your-app-name.onrender.com/status/${downloadInfo.download_id}`);
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
        // Download is ready
        window.location.href = `https://your-app-name.onrender.com/download/${downloadInfo.download_id}`;
    } else if (status.status === 'downloading') {
        // Show progress
        console.log(`Progress: ${status.progress}%`);
        setTimeout(checkStatus, 2000); // Check again in 2 seconds
    }
};
checkStatus();
```

## Troubleshooting

### Common Issues

1. **Build Fails:**
   - Check `requirements.txt` for correct package versions
   - Ensure Python version compatibility

2. **App Crashes on Start:**
   - Check logs in Render dashboard
   - Verify start command is correct
   - Check for missing dependencies

3. **Slow Performance:**
   - Free tier has limitations
   - Consider upgrading to paid plan
   - Optimize worker count

4. **Download Timeouts:**
   - Large files may timeout on free tier
   - Increase timeout in gunicorn command
   - Consider chunked downloads

### Debugging

1. **Check Render Logs:**
   - Go to service dashboard
   - Click "Logs" tab
   - Look for error messages

2. **Test Locally First:**
   ```bash
   python test_api.py
   ```

3. **Verify Dependencies:**
   ```bash
   pip install -r requirements.txt
   python -c "import yt_dlp; print('yt-dlp works')"
   ```

### Performance Optimization

1. **Increase Workers:**
   ```
   gunicorn --bind 0.0.0.0:$PORT app:app --timeout 300 --workers 4
   ```

2. **Add Caching:**
   - Implement Redis for caching extraction results
   - Cache video metadata

3. **Optimize Memory:**
   - Stream downloads instead of loading in memory
   - Clean up temporary files regularly

## Security Considerations

1. **Rate Limiting:**
   - Implement rate limiting for production
   - Use Flask-Limiter

2. **Input Validation:**
   - Validate URLs before processing
   - Sanitize user inputs

3. **HTTPS Only:**
   - Render provides HTTPS by default
   - Redirect HTTP to HTTPS

4. **Environment Variables:**
   - Store sensitive data in environment variables
   - Never commit secrets to repository

## Monitoring

1. **Health Checks:**
   - Use `/health` endpoint for monitoring
   - Set up uptime monitoring

2. **Logs:**
   - Monitor application logs
   - Set up log aggregation

3. **Metrics:**
   - Track API usage
   - Monitor download success rates

## Scaling

1. **Horizontal Scaling:**
   - Increase worker count
   - Use multiple service instances

2. **Database:**
   - Add PostgreSQL for persistent storage
   - Store download history

3. **File Storage:**
   - Use cloud storage (S3, GCS)
   - Implement CDN for downloads

## Support

If you encounter issues:

1. Check the logs in Render dashboard
2. Test locally with `python test_api.py`
3. Review the troubleshooting section
4. Check GitHub issues for similar problems

## Next Steps

After successful deployment:

1. **Add Authentication:** Implement API keys or OAuth
2. **Add Database:** Store download history and user preferences
3. **Add Queue System:** Use Celery for background processing
4. **Add Monitoring:** Implement comprehensive logging and metrics
5. **Add Tests:** Create comprehensive test suite