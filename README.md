# contemporary art rss scraper

From a set of rss feeds, pull the content into an Arpedia compatible ingest format

rss feed sources:

- http://www.artsjournal.com/feed
- http://www.artnews.com/feed/
- http://theartnewspaper.com/rss/
- http://www.vogue.com/tag/misc/contemporary-art/rss
- http://feeds.feedburner.com/Wallpaperfeed
- https://www.youtube.com/feeds/videos.xml?channel_id=UCpYHEAhSUx1hBn2SkvXvTrg
- http://feeds.feedburner.com/Wallpaperfeed

For Youtube - steps to get RSS feed for a channel:

- Go to the YouTube channel you want to track
- View the page’s source code
- Look for the following text: channel-external-id
- Get the value for that element (it’ll look something like UCBcRF18a7Qf58cCRy5xuWwQ
- Replace that value into this URL: 

```https://www.youtube.com/feeds/videos.xml?channel_id=<channel-external-id>```
