# EPG to M3U Icons

A simple Python Flask server that merges channel icons from an EPG (XMLTV) file into an M3U playlist. This allows you to enhance your M3U playlists with channel logos from your EPG guide.

## Features

- Fetches M3U playlists and EPG files from URLs on-demand
- Parses XMLTV/EPG format to extract channel icons
- Matches channels using multiple strategies (tvg-id, tvg-name, channel name)
- Updates or adds `tvg-logo` attributes to M3U entries
- Serves the merged playlist via HTTP for use in IPTV players

## Installation

1. Install Python 3.7 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

### Access your merged playlist:

Use the following URL format in your IPTV player:
```
http://localhost:5000/playlist.m3u?m3u=<M3U_URL>&epg=<EPG_URL>
```

**Parameters:**
- `m3u` - URL to your M3U playlist (URL encoded if needed)
- `epg` - URL to your EPG/XMLTV file (URL encoded if needed)

### Example:
```
http://localhost:5000/playlist.m3u?m3u=http://example.com/playlist.m3u&epg=http://example.com/epg.xml
```

## How It Works

1. The server receives a request with M3U and EPG URLs
2. Fetches both files from the provided URLs
3. Parses the EPG to extract channel icons
4. Parses the M3U playlist entries
5. Matches channels between M3U and EPG using:
   - `tvg-id` attribute
   - `tvg-name` attribute
   - Channel display name
6. Updates the `tvg-logo` attribute in M3U entries with icons from the EPG
7. Returns the modified M3U playlist

## Deployment

### Local Network Access

To make the server accessible on your local network, it already binds to `0.0.0.0`, so you can access it from other devices using:
```
http://<your-computer-ip>:5000/playlist.m3u?m3u=...&epg=...
```

### Production Deployment

For production use, consider:
- Using a production WSGI server like `gunicorn`:
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 app:app
  ```
- Setting up a reverse proxy (nginx, Apache)
- Enabling HTTPS
- Adding caching if needed
- Using environment variables for configuration

## Troubleshooting

- **No icons appearing**: Check that your EPG file contains `<icon src="..."/>` elements in channel definitions
- **Channels not matching**: The script tries multiple matching strategies, but ensure your M3U has proper `tvg-id` or `tvg-name` attributes that match the EPG
- **Timeout errors**: Increase the timeout in `fetch_url()` if your M3U or EPG files are large

## License

MIT License - Feel free to use and modify as needed.
