# Video Extractor API

A Flask-based web API that extracts and downloads videos from streaming websites. Deployable on Render with a simple web interface.

## Features

- 🎥 Extract video sources from streaming websites
- ⬇️ Download videos with progress tracking
- 🌐 RESTful API with JSON responses
- 🖥️ Simple web interface for testing
- 🚀 Ready for Render deployment
- 📊 Real-time download progress
- 🔄 Multiple extraction methods (yt-dlp, direct parsing, iframe analysis)

## API Endpoints

### GET `/`
API documentation and usage information

### POST `/extract`
Extract video sources from a URL
```json
{
  "url": "https://example.com/video"
}
```

Response:
```json
{
  "success": true,
  "url": "https://example.com/video",
  "sources_found": 2,
  "sources": [
    {
      "url": "https://cdn.example.com/video.mp4",
      "quality": 1080,
      "format": "mp4",
      "method": "yt-dlp",
      "title": "Video Title",
      "filesize": 567890123,
      "duration": 3600
    }
  ]
}
```

### POST `/download`
Start video download
```json
{
  "url": "https://example.com/video",
  "quality": "best"
}
```

Quality options: `"best"`, `"worst"`, `"1080"`, `"720"`, `"480"`, `"360"`

Response:
```json
{
  "success": true,
  "download_id": "uuid-here",
  "selected_source": {
    "url": "https://cdn.example.com/video.mp4",
    "quality": 1080,
    "format": "mp4",
    "method": "yt-dlp"
  },
  "status_url": "/status/uuid-here",
  "download_url": "/download/uuid-here"
}
```

### GET `/status/<download_id>`
Check download progress
```json
{
  "status": "downloading",
  "progress": 45.2,
  "message": "Downloading... (Size: 541.78 MB)",
  "started_at": "2024-01-01T12:00:00",
  "downloaded": 257890123,
  "total_size": 567890123
}
```

### GET `/download/<download_id>`
Download the completed file (returns file stream)

### POST `/cancel/<download_id>`
Cancel an ongoing download

### GET `/health`
Health check endpoint

## Deployment on Render

### Method 1: Direct GitHub Deployment

1. **Fork/Clone this repository**
2. **Push to your GitHub account**
3. **Connect to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select this repository

4. **Configure the service:**
   - **Name:** `video-extractor-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app --timeout 300 --workers 2`
   - **Instance Type:** Free tier is sufficient for testing

5. **Deploy:** Click "Create Web Service"

### Method 2: Manual Deployment

1. **Create a new Web Service on Render**
2. **Upload these files:**
   - `app.py`
   - `simple_video_extractor.py`
   - `requirements.txt`
   - `Procfile`
   - `runtime.txt`
   - `templates/index.html`

3. **Set environment variables (optional):**
   - `PYTHON_VERSION=3.11.0`

## Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python app.py
```

3. **Access the API:**
   - Web interface: `http://localhost:5000`
   - API endpoints: `http://localhost:5000/extract`, etc.

## Usage Examples

### Using cURL

**Extract sources:**
```bash
curl -X POST http://your-app.onrender.com/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video"}'
```

**Start download:**
```bash
curl -X POST http://your-app.onrender.com/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video", "quality": "best"}'
```

**Check status:**
```bash
curl http://your-app.onrender.com/status/your-download-id
```

### Using Python

```python
import requests

# Extract sources
response = requests.post('http://your-app.onrender.com/extract', 
                        json={'url': 'https://example.com/video'})
sources = response.json()

# Start download
response = requests.post('http://your-app.onrender.com/download',
                        json={'url': 'https://example.com/video', 'quality': 'best'})
download_info = response.json()
download_id = download_info['download_id']

# Check status
status_response = requests.get(f'http://your-app.onrender.com/status/{download_id}')
status = status_response.json()

# Download file when completed
if status['status'] == 'completed':
    file_response = requests.get(f'http://your-app.onrender.com/download/{download_id}')
    with open('video.mp4', 'wb') as f:
        f.write(file_response.content)
```

## Supported Sites

The extractor supports various streaming platforms through multiple extraction methods:

- **yt-dlp supported sites:** YouTube, Vimeo, Dailymotion, and 1000+ others
- **Direct extraction:** Sites with embedded video players
- **Iframe analysis:** Sites using iframe-based players
- **JavaScript parsing:** Sites with JS-generated video URLs
- **API endpoint detection:** Sites using AJAX for video loading

## Configuration

### Environment Variables

- `PORT`: Server port (default: 5000)
- `PYTHON_VERSION`: Python version for Render

### Timeouts and Limits

- Request timeout: 30 seconds
- Download timeout: 300 seconds (5 minutes)
- Worker processes: 2
- File cleanup: 1 hour after download

## Troubleshooting

### Common Issues

1. **"No video sources found"**
   - Check if the URL is accessible
   - Try with a different video URL
   - Some sites may require specific headers or cookies

2. **Download fails**
   - The video URL might be protected or expired
   - Try extracting sources first to verify availability

3. **Slow downloads**
   - Large files may take time on free tier
   - Consider upgrading Render instance for better performance

### Logs

Check Render logs for detailed error information:
- Go to your service dashboard
- Click on "Logs" tab
- Look for error messages and stack traces

## Security Notes

- The API doesn't store user data permanently
- Downloaded files are cleaned up automatically
- Use HTTPS in production
- Consider rate limiting for production use

## License

This project is for educational purposes. Respect website terms of service and copyright laws when using this tool.