"""Build XMLTV for exact channel-ID matches; never add or change stream URLs."""
import copy
import gzip
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCALNOW = 'https://data-store-trans-cdn.api.cms.amdvids.com/live/epg/US/website'
XUMO = 'https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz'
GUIDE_URL = 'https://raw.githubusercontent.com/abercrombie9585/parents-boston-tv/main/guide.xml'

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()

def stamp(value):
    return datetime.fromtimestamp(float(value), timezone.utc).strftime('%Y%m%d%H%M%S %z')

def parse(value):
    return datetime.strptime(value, '%Y%m%d%H%M%S %z')

def main():
    now = datetime.now(timezone.utc)
    lines = (ROOT / 'parents-boston-tv.m3u').read_text(encoding='utf-8-sig').splitlines()
    entries = []
    for line in lines:
        if line.startswith('#EXTINF:'):
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', line))
            # Separate display name at the first comma outside quoted attributes.
            name = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', line, maxsplit=1)[1]
            entries.append((attrs.get('tvg-id', ''), name, attrs.get('group-title', '')))
    wanted = {cid for cid, _, _ in entries if cid}
    programmes = {}
    errors = []
    def add(programme):
        cid = programme.get('channel')
        try:
            if cid not in wanted or parse(programme.get('stop', '')) <= now:
                return
            if parse(programme.get('start', '')) >= parse(programme.get('stop', '')):
                return
        except (ValueError, TypeError):
            return
        if not programme.findtext('title'):
            return
        key = (cid, programme.get('start'), programme.get('stop'), programme.findtext('title'))
        programmes[key] = programme

    try:
        payload = fetch(LOCALNOW)
        data = json.loads(gzip.decompress(payload) if payload.startswith(b'\x1f\x8b') else payload)
        for channel in data['channels']:
            cid = 'LN_' + str(channel['_id'])
            if cid not in wanted:
                continue
            for item in channel.get('program', []):
                if not all(item.get(k) is not None for k in ['starts_at', 'ends_at', 'program_title']):
                    continue
                p = ET.Element('programme', channel=cid, start=stamp(item['starts_at']), stop=stamp(item['ends_at']))
                ET.SubElement(p, 'title', lang='en').text = item['program_title']
                if item.get('program_description'):
                    ET.SubElement(p, 'desc', lang='en').text = item['program_description']
                add(p)
    except Exception as exc:
        errors.append('LocalNow: ' + str(exc))

    try:
        source = ET.fromstring(gzip.decompress(fetch(XUMO)))
        for original in source.findall('programme'):
            p = copy.deepcopy(original)
            cid = p.get('channel', '')
            p.set('channel', cid if cid.startswith('XUMO_') else 'XUMO_' + cid)
            add(p)
    except Exception as exc:
        errors.append('Xumo: ' + str(exc))

    # Preserve still-valid existing listings when a source is temporarily unavailable.
    existing = ROOT / 'guide.xml'
    if existing.exists():
        fresh_channels = {key[0] for key in programmes}
        for p in ET.parse(existing).getroot().findall('programme'):
            key = (p.get('channel'), p.get('start'), p.get('stop'), p.findtext('title'))
            if p.get('channel') not in fresh_channels and key not in programmes:
                add(p)
    if not programmes:
        raise RuntimeError('No current schedules; refusing to replace the guide. ' + '; '.join(errors))
    covered = {key[0] for key in programmes}
    tv = ET.Element('tv', {'generator-info-name': 'Parents Boston TV', 'date': stamp(now.timestamp())})
    channel_names = dict((cid, name) for cid, name, _ in entries if cid in covered)
    for cid, name in sorted(channel_names.items()):
        channel = ET.SubElement(tv, 'channel', id=cid)
        ET.SubElement(channel, 'display-name').text = name
    for _, p in sorted(programmes.items()):
        tv.append(p)
    ET.indent(tv)
    xml = ET.tostring(tv, encoding='utf-8', xml_declaration=True)
    ET.fromstring(xml)
    existing.write_bytes(xml + b'\n')
    lines[0] = '#EXTM3U x-tvg-url="' + GUIDE_URL + '"'
    (ROOT / 'parents-boston-tv.m3u').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    groups = {}
    for cid, _, group in entries:
        source_name = 'LocalNow' if group.startswith('LocalNow') else 'XUMO' if group.startswith('XUMO') else 'FreeLiveSports' if group.startswith('FreeLiveSports') else 'Massachusetts'
        stat = groups.setdefault(source_name, {'entries': 0, 'with_future_listings': 0})
        stat['entries'] += 1
        stat['with_future_listings'] += int(cid in covered)
    report = {'updated_utc': now.isoformat(), 'programmes': len(programmes), 'groups': groups,
              'latest_programme_end': max(p.get('stop') for p in programmes.values()),
              'source_errors': errors,
              'uncovered': [{'name': name, 'group': group} for cid, name, group in entries if cid not in covered]}
    (ROOT / 'guide-status.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'uncovered'}, indent=2))
    if errors:
        raise RuntimeError('; '.join(errors))

if __name__ == '__main__':
    main()
