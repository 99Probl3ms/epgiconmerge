#!/usr/bin/env python3
"""
EPG to M3U Icons - Merge channel icons from EPG into M3U playlists
"""
import re
import xml.etree.ElementTree as ET
from flask import Flask, Response, request
import requests
from urllib.parse import unquote

app = Flask(__name__)


def fetch_url(url):
    """Fetch content from a URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch {url}: {str(e)}")


def parse_epg(epg_content):
    """Parse EPG/XMLTV and extract channel icons

    Returns:
        dict: Mapping of channel ID to icon URL
    """
    icon_map = {}

    try:
        root = ET.fromstring(epg_content)

        # Find all channel elements
        for channel in root.findall('.//channel'):
            channel_id = channel.get('id')
            if not channel_id:
                continue

            # Look for icon element
            icon = channel.find('icon')
            if icon is not None and icon.get('src'):
                icon_map[channel_id.lower()] = icon.get('src')

            # Also map display-name to icon for matching
            for display_name in channel.findall('display-name'):
                if display_name.text:
                    icon_map[display_name.text.lower()] = icon.get('src') if icon is not None else None

    except ET.ParseError as e:
        raise Exception(f"Failed to parse EPG XML: {str(e)}")

    return icon_map


def parse_m3u(m3u_content):
    """Parse M3U playlist into entries

    Returns:
        list: List of tuples (extinf_line, url_line)
    """
    lines = m3u_content.strip().split('\n')
    entries = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('#EXTINF:'):
            extinf_line = line
            # Get the next non-empty, non-comment line as the URL
            i += 1
            while i < len(lines):
                url_line = lines[i].strip()
                if url_line and not url_line.startswith('#'):
                    entries.append((extinf_line, url_line))
                    break
                elif url_line.startswith('#'):
                    # Skip other comment lines
                    i += 1
                else:
                    i += 1
        i += 1

    return entries


def extract_channel_info(extinf_line):
    """Extract channel information from EXTINF line

    Returns:
        dict: Channel info including tvg-id, tvg-name, group-title, and channel-name
    """
    info = {
        'tvg-id': None,
        'tvg-name': None,
        'tvg-logo': None,
        'group-title': None,
        'channel-name': None
    }

    # Extract tvg-id
    tvg_id_match = re.search(r'tvg-id="([^"]*)"', extinf_line)
    if tvg_id_match:
        info['tvg-id'] = tvg_id_match.group(1)

    # Extract tvg-name
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', extinf_line)
    if tvg_name_match:
        info['tvg-name'] = tvg_name_match.group(1)

    # Extract tvg-logo
    tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', extinf_line)
    if tvg_logo_match:
        info['tvg-logo'] = tvg_logo_match.group(1)

    # Extract group-title
    group_match = re.search(r'group-title="([^"]*)"', extinf_line)
    if group_match:
        info['group-title'] = group_match.group(1)

    # Extract channel name (after the last comma)
    name_match = re.search(r',(.+)$', extinf_line)
    if name_match:
        info['channel-name'] = name_match.group(1).strip()

    return info


def update_extinf_logo(extinf_line, new_logo_url):
    """Update or add tvg-logo attribute in EXTINF line"""
    # Check if tvg-logo already exists
    if 'tvg-logo=' in extinf_line:
        # Replace existing tvg-logo
        return re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{new_logo_url}"', extinf_line)
    else:
        # Add tvg-logo after #EXTINF:
        # Insert after the duration (e.g., #EXTINF:-1 or #EXTINF:0)
        match = re.match(r'(#EXTINF:[^,\s]+\s*)(.*)', extinf_line)
        if match:
            return f'{match.group(1)}tvg-logo="{new_logo_url}" {match.group(2)}'
        else:
            # Fallback: just append before the comma
            return extinf_line.replace(',', f' tvg-logo="{new_logo_url}",', 1)


def merge_m3u_with_epg_icons(m3u_content, epg_content):
    """Merge M3U playlist with icons from EPG

    Returns:
        str: Modified M3U content with updated icons
    """
    # Parse EPG to get icon mapping
    icon_map = parse_epg(epg_content)

    # Parse M3U entries
    entries = parse_m3u(m3u_content)

    # Build new M3U content
    result_lines = ['#EXTM3U']

    matched_count = 0
    total_count = len(entries)

    for extinf_line, url_line in entries:
        channel_info = extract_channel_info(extinf_line)

        # Try to find icon using various matching strategies
        new_logo = None

        # Strategy 1: Match by tvg-id
        if channel_info['tvg-id'] and channel_info['tvg-id'].lower() in icon_map:
            new_logo = icon_map[channel_info['tvg-id'].lower()]

        # Strategy 2: Match by tvg-name
        if not new_logo and channel_info['tvg-name'] and channel_info['tvg-name'].lower() in icon_map:
            new_logo = icon_map[channel_info['tvg-name'].lower()]

        # Strategy 3: Match by channel-name
        if not new_logo and channel_info['channel-name'] and channel_info['channel-name'].lower() in icon_map:
            new_logo = icon_map[channel_info['channel-name'].lower()]

        # Update logo if found
        if new_logo:
            extinf_line = update_extinf_logo(extinf_line, new_logo)
            matched_count += 1

        result_lines.append(extinf_line)
        result_lines.append(url_line)

    print(f"Matched {matched_count} out of {total_count} channels with EPG icons")

    return '\n'.join(result_lines)


@app.route('/playlist.m3u')
def serve_playlist():
    """Serve the merged M3U playlist"""
    # Get M3U and EPG URLs from query parameters
    m3u_url = request.args.get('m3u')
    epg_url = request.args.get('epg')

    if not m3u_url:
        return "Error: 'm3u' parameter is required", 400

    if not epg_url:
        return "Error: 'epg' parameter is required", 400

    try:
        # Fetch M3U and EPG
        print(f"Fetching M3U from: {m3u_url}")
        m3u_content = fetch_url(m3u_url)

        print(f"Fetching EPG from: {epg_url}")
        epg_content = fetch_url(epg_url)

        # Merge icons
        print("Merging M3U with EPG icons...")
        merged_content = merge_m3u_with_epg_icons(m3u_content, epg_content)

        # Return as M3U file
        return Response(merged_content, mimetype='application/x-mpegurl')

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/')
def index():
    """Show usage information"""
    return """
    <h1>EPG to M3U Icons Merger</h1>
    <p>This service merges channel icons from an EPG into an M3U playlist.</p>

    <h2>Usage:</h2>
    <pre>GET /playlist.m3u?m3u=&lt;M3U_URL&gt;&epg=&lt;EPG_URL&gt;</pre>

    <h3>Parameters:</h3>
    <ul>
        <li><strong>m3u</strong> - URL to your M3U playlist (URL encoded)</li>
        <li><strong>epg</strong> - URL to your EPG/XMLTV file (URL encoded)</li>
    </ul>

    <h3>Example:</h3>
    <pre>/playlist.m3u?m3u=http://example.com/playlist.m3u&epg=http://example.com/epg.xml</pre>

    <p>Use the resulting URL in your IPTV player to get your playlist with updated channel icons.</p>
    """


if __name__ == '__main__':
    # Run the server
    print("Starting EPG to M3U Icons server...")
    print("Server will be available at: http://localhost:5000")
    print("\nUsage: http://localhost:5000/playlist.m3u?m3u=<M3U_URL>&epg=<EPG_URL>")
    app.run(host='0.0.0.0', port=5000, debug=True)
