# Parents Boston TV

Playlist URL:
https://raw.githubusercontent.com/abercrombie9585/parents-boston-tv/main/parents-boston-tv.m3u

EPG / XMLTV guide URL:
https://raw.githubusercontent.com/abercrombie9585/parents-boston-tv/main/guide.xml

Use the M3U URL as the playlist and the XMLTV URL as the EPG in your player. Reload the playlist after adding the guide. Times are supplied in UTC; the player displays local times.

## Guide coverage and updates

The guide matches LocalNow IDs exactly and maps Xumo numeric IDs to the playlist's `XUMO_` IDs. It does not guess by channel name. Massachusetts and FreeLiveSports currently have no mapped schedules. Some LocalNow and Xumo channels may also have no current listings. See [guide-status.json](guide-status.json) for current coverage and missing channels.

Listings come from the public LocalNow schedule endpoint and [BuddyChewChew's Xumo guide](https://github.com/BuddyChewChew/xumo-playlist-generator). The guide refreshes hourly because LocalNow supplies only a short rolling schedule. GitHub schedules can be delayed; upstream outages or stale data may leave gaps. GitHub may disable scheduled workflows after extended repository inactivity. The workflow can also be run manually from Actions. No schedules are invented.

## Playlist sources

- https://iptv-org.github.io/iptv/subdivisions/us-ma.m3u
- https://www.apsattv.com/localnow.m3u
- https://www.apsattv.com/freelivesports.m3u
- https://www.apsattv.com/xumo.m3u

The playlist is a snapshot of those four sources. Guide updates do not refresh or add stream URLs. Availability depends on the original providers. No video is hosted here.
