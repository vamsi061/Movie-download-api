#!/usr/bin/env python3
"""
Video Extractor API - Flask web service for video extraction and downloading
Deployable on Render with POST endpoint for video URL processing
"""

from flask import Flask, request, jsonify, send_file, Response, render_template
from flask_cors import CORS
import os
import tempfile
import threading
import time
from datetime import datetime
import uuid
import requests
from simple_video_extractor import SimpleVideoExtractor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global storage for download status
download_status = {}
download_files = {}

class VideoDownloadManager:
    def __init__(self):
        self.extractor = SimpleVideoExtractor()
        self.temp_dir = tempfile.mkdtemp()
        
    def extract_sources(self, url):
        """Extract video sources from URL"""
        try:
            sources = self.extractor.extract_video_sources(url)
            return sources
        except Exception as e:
            logger.error(f"Source extraction failed: {e}")
            return []
    
    def download_video_async(self, download_id, video_source, output_path):
        """Download video asynchronously and update status"""
        try:
            # Initialize status - make sure it's set before any processing
            download_status[download_id] = {
                'status': 'initializing',
                'progress': 0,
                'message': 'Initializing download...',
                'started_at': datetime.now().isoformat(),
                'file_path': output_path,
                'download_id': download_id,
                'source_url': video_source['url'][:100] + '...' if len(video_source['url']) > 100 else video_source['url']
            }
            
            # Update to downloading status
            download_status[download_id].update({
                'status': 'downloading',
                'message': 'Starting download...'
            })
            
            # Custom download with progress tracking
            url = video_source['url']
            
            # Enhanced headers for protected downloads
            download_headers = self.extractor.session.headers.copy()
            if self.extractor.original_url:
                download_headers['Referer'] = self.extractor.original_url
            
            download_headers.update({
                'Range': 'bytes=0-',
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
            })
            
            response = self.extractor.session.get(url, headers=download_headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            download_status[download_id]['total_size'] = total_size
            download_status[download_id]['message'] = f'Downloading... (Size: {total_size / (1024*1024):.2f} MB)'
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            download_status[download_id]['progress'] = progress
                            download_status[download_id]['downloaded'] = downloaded
                        
                        # Check if download was cancelled
                        if download_status[download_id].get('cancelled', False):
                            break
            
            if downloaded > 0 and not download_status[download_id].get('cancelled', False):
                download_status[download_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Download completed successfully!',
                    'completed_at': datetime.now().isoformat(),
                    'file_size': downloaded,
                    'file_ready': True
                })
                download_files[download_id] = output_path
                logger.info(f"Download {download_id} completed successfully. File: {output_path}")
            else:
                download_status[download_id].update({
                    'status': 'failed',
                    'message': 'Download was cancelled or failed',
                    'completed_at': datetime.now().isoformat(),
                    'file_ready': False
                })
                logger.error(f"Download {download_id} failed or was cancelled")
                
        except Exception as e:
            logger.error(f"Download {download_id} failed: {e}")
            # Ensure the download_id exists in status before updating
            if download_id not in download_status:
                download_status[download_id] = {
                    'download_id': download_id,
                    'started_at': datetime.now().isoformat()
                }
            
            download_status[download_id].update({
                'status': 'failed',
                'progress': 0,
                'message': f'Download failed: {str(e)}',
                'completed_at': datetime.now().isoformat(),
                'file_ready': False,
                'error': str(e)
            })

# Global download manager
download_manager = VideoDownloadManager()

@app.route('/', methods=['GET'])
def home():
    """Serve the web interface"""
    # Check if request wants JSON (API documentation)
    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            'name': 'Video Extractor API',
            'version': '1.0.0',
            'description': 'Extract and download videos from streaming websites',
            'endpoints': {
                'POST /extract': 'Extract video sources from URL',
                'POST /download': 'Start video download',
                'GET /status/<download_id>': 'Check download status',
                'GET /download/<download_id>': 'Download completed file',
                'GET /health': 'Health check'
            },
            'usage': {
                'extract': {
                    'method': 'POST',
                    'body': {'url': 'https://example.com/video'},
                    'response': 'List of video sources with URLs and metadata'
                },
                'download': {
                    'method': 'POST', 
                    'body': {'url': 'https://example.com/video', 'quality': 'best'},
                    'response': 'Download ID for tracking progress'
                }
            }
        })
    else:
        # Serve the HTML interface
        return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_downloads': len([d for d in download_status.values() if d['status'] == 'downloading'])
    })

@app.route('/extract', methods=['POST'])
def extract_sources():
    """Extract video sources from URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        logger.info(f"Extracting sources from: {url}")
        
        sources = download_manager.extract_sources(url)
        
        if not sources:
            return jsonify({
                'error': 'No video sources found',
                'url': url,
                'sources': []
            }), 404
        
        # Format sources for API response
        formatted_sources = []
        for source in sources:
            formatted_sources.append({
                'url': source['url'],
                'quality': source['quality'],
                'format': source['format'],
                'method': source['method'],
                'title': source['title'],
                'filesize': source.get('filesize', 0),
                'duration': source.get('duration', 0)
            })
        
        return jsonify({
            'success': True,
            'url': url,
            'sources_found': len(formatted_sources),
            'sources': formatted_sources
        })
        
    except Exception as e:
        logger.error(f"Source extraction error: {e}")
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def start_download():
    """Start video download"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        quality_preference = data.get('quality', 'best')  # 'best', 'worst', or specific quality like '720'
        
        logger.info(f"Starting download from: {url}")
        
        # Extract sources first
        sources = download_manager.extract_sources(url)
        
        if not sources:
            return jsonify({
                'error': 'No video sources found',
                'url': url
            }), 404
        
        # Filter out invalid URLs first
        valid_sources = []
        for source in sources:
            url = source['url']
            # Check if URL is properly formatted and accessible
            if (url.startswith(('http://', 'https://')) and 
                not url.startswith(',//') and 
                '|' not in url and
                len(url) > 20):  # Reasonable URL length
                valid_sources.append(source)
        
        if not valid_sources:
            return jsonify({
                'error': 'No valid video sources found. All extracted URLs are malformed.',
                'url': url,
                'extracted_sources': len(sources),
                'valid_sources': 0
            }), 404
        
        # Select best source based on quality preference from valid sources
        selected_source = None
        if quality_preference == 'best':
            # Sort by quality, then by URL reliability (prefer direct file URLs)
            valid_sources.sort(key=lambda x: (x['quality'], 1 if '.mp4' in x['url'] else 0), reverse=True)
            selected_source = valid_sources[0]
        elif quality_preference == 'worst':
            selected_source = min(valid_sources, key=lambda x: x['quality'])
        else:
            # Try to find specific quality
            try:
                target_quality = int(quality_preference)
                # Find closest quality from valid sources
                selected_source = min(valid_sources, key=lambda x: abs(x['quality'] - target_quality))
            except ValueError:
                selected_source = valid_sources[0]  # Default to first valid source
        
        if not selected_source:
            selected_source = valid_sources[0]
        
        # Generate download ID
        download_id = str(uuid.uuid4())
        
        # Create output filename
        title = selected_source.get('title', 'video').replace(' ', '_')
        title = ''.join(c for c in title if c.isalnum() or c in '-_.')[:50]  # Clean filename
        format_ext = selected_source.get('format', 'mp4')
        output_filename = f"{title}_{download_id[:8]}.{format_ext}"
        output_path = os.path.join(download_manager.temp_dir, output_filename)
        
        # Start download in background thread
        download_thread = threading.Thread(
            target=download_manager.download_video_async,
            args=(download_id, selected_source, output_path)
        )
        download_thread.daemon = True
        download_thread.start()
        
        return jsonify({
            'success': True,
            'download_id': download_id,
            'selected_source': {
                'url': selected_source['url'][:100] + '...' if len(selected_source['url']) > 100 else selected_source['url'],
                'quality': selected_source['quality'],
                'format': selected_source['format'],
                'method': selected_source['method']
            },
            'total_sources_found': len(sources),
            'valid_sources_found': len(valid_sources),
            'status_url': f'/status/{download_id}',
            'download_url': f'/download/{download_id}',
            'message': 'Download started. Use status_url to track progress.'
        })
        
    except Exception as e:
        logger.error(f"Download start error: {e}")
        return jsonify({'error': f'Download failed to start: {str(e)}'}), 500

@app.route('/status/<download_id>', methods=['GET'])
def get_download_status(download_id):
    """Get download status"""
    if download_id not in download_status:
        logger.warning(f"Status requested for unknown download ID: {download_id}")
        return jsonify({
            'error': 'Download ID not found',
            'download_id': download_id,
            'message': 'This download ID does not exist or has been cleaned up',
            'status': 'not_found'
        }), 404
    
    status = download_status[download_id].copy()
    
    # Add additional info for completed downloads
    if status['status'] == 'completed' and download_id in download_files:
        file_path = download_files[download_id]
        if os.path.exists(file_path):
            status['file_ready'] = True
            if 'file_size' not in status:
                status['file_size'] = os.path.getsize(file_path)
        else:
            status['file_ready'] = False
            status['message'] = 'Download completed but file not found'
    
    logger.info(f"Status check for {download_id}: {status['status']} - {status.get('progress', 0)}%")
    return jsonify(status)

@app.route('/download/<download_id>', methods=['GET'])
def download_file(download_id):
    """Download the completed file"""
    if download_id not in download_files:
        return jsonify({'error': 'Download not found or not completed'}), 404
    
    file_path = download_files[download_id]
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Get original filename
    filename = os.path.basename(file_path)
    
    def generate():
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                yield data
    
    return Response(
        generate(),
        mimetype='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(os.path.getsize(file_path))
        }
    )

@app.route('/cancel/<download_id>', methods=['POST'])
def cancel_download(download_id):
    """Cancel an ongoing download"""
    if download_id not in download_status:
        return jsonify({'error': 'Download ID not found'}), 404
    
    if download_status[download_id]['status'] == 'downloading':
        download_status[download_id]['cancelled'] = True
        download_status[download_id]['status'] = 'cancelled'
        download_status[download_id]['message'] = 'Download cancelled by user'
        return jsonify({'success': True, 'message': 'Download cancelled'})
    else:
        return jsonify({'error': 'Download is not active'}), 400

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up old download files (admin endpoint)"""
    try:
        cleaned_count = 0
        current_time = time.time()
        
        # Clean up files older than 1 hour
        for download_id, file_path in list(download_files.items()):
            if os.path.exists(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > 3600:  # 1 hour
                    os.remove(file_path)
                    del download_files[download_id]
                    if download_id in download_status:
                        del download_status[download_id]
                    cleaned_count += 1
        
        return jsonify({
            'success': True,
            'cleaned_files': cleaned_count,
            'active_downloads': len(download_files)
        })
        
    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)