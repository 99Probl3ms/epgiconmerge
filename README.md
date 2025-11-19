# EPG to M3U Icons

A simple Python Flask server that merges channel icons from an EPG (XMLTV) file into an M3U playlist. This allows you to enhance your M3U playlists with channel logos from your EPG guide.

## Features

- Fetches M3U playlists and EPG files from URLs on-demand
- Parses XMLTV/EPG format to extract channel icons
- Matches channels using multiple strategies (tvg-id, tvg-name, channel name)
- Updates or adds `tvg-logo` attributes to M3U entries
- Serves the merged playlist via HTTP for use in IPTV players
- Web-based settings page to configure and save your URLs
- Persistent configuration using .env file

## Installation

1. Install Python 3.7 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your URLs (choose one option):

   **Option A: Using the Web Interface (Recommended)**
   - Start the server and visit `http://localhost:5000/settings`
   - Enter your M3U and EPG URLs in the form
   - Click "Save Settings"

   **Option B: Using .env file**
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your URLs:
   ```bash
   M3U_URL=http://example.com/playlist.m3u
   EPG_URL=http://example.com/epg.xml
   ```

## Usage

### Start the server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

### Access your merged playlist:

**Option 1: Using Configured URLs (Easiest)**

After configuring your URLs in the settings or `.env` file, simply use:
```
http://localhost:5000/playlist.m3u
```

**Option 2: Using Query Parameters**

You can override or provide URLs directly via query parameters:
```
http://localhost:5000/playlist.m3u?m3u=<M3U_URL>&epg=<EPG_URL>
```

**Parameters:**
- `m3u` - URL to your M3U playlist (optional if configured in .env)
- `epg` - URL to your EPG/XMLTV file (optional if configured in .env)

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
