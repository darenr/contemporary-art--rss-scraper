# -*- coding: utf-8 -*-


import json
import codecs
import traceback
import sys
import requests
import requests_cache
import feedparser
import collections
from bs4 import BeautifulSoup
from urlparse import urlparse, urljoin

one_day = 60 * 60 * 24
requests_cache.install_cache(
    'rss_cache', backend='sqlite', expire_after=one_day)

headers = {
    'User-Agent': 'Mozilla/5.0'
}

def get_entry_formatted(mime_type, value):
    if mime_type.lower() == 'text/html':
        soup = BeautifulSoup(value, 'html5lib')
        return ''.join(line.lstrip() for line in soup.getText().splitlines(True))
    else:
        return value;

def parse_content(mime_type, value):
    if mime_type.lower() == 'text/html':
        soup = BeautifulSoup(value, 'html5lib')

        # scoop up all the text
        result = {
            "text": ''.join(line.lstrip() for line in soup.getText().splitlines(True))
        }

        if soup.find('img'):
            result['imgurl'] = soup.find('img')['src']

        return result
    else:
        return value

def get_entry_value(entry, key, feed):
    #
    # deals with differences between feeds
    #
    _key = feed['fields'][key] if 'fields' in feed and key in feed['fields'] else key
    if _key in entry:
        return entry[_key]
    else:
        print ' *', 'No', _key, "field in", entry
        return None

def fetch_page_and_parse(feed, url):
    print ' *', 'parsing page link:', url
    page = requests.get(url, headers=headers)
    result = {}

    if page.status_code == 200:

        soup = BeautifulSoup(page.text, 'html5lib')

        if 'selector' in feed:
            for img in soup.select(feed['selector']):
                src = img['src'] if img.has_attr('src') else None
                if not src:
                    src = img['srcset'] if img.has_attr('srcset') else None
                if src:
                    if src.startswith('/'):
                        result['imgurl'] = urljoin(feed['url'], src)
                    else:
                        result['imgurl'] = src
                    break
        else:
            # look for og_image as the default
            if soup.find('meta', {"property": "og:image"}):
                if 'content' in soup.find('meta', {"property": "og:image"}):
                    result['imgurl'] = soup.find('meta', {"property": "og:image"})['content']

    return result

def validate(record):
    mandatory_fields = ['imgurl', 'description', 'title', 'link']

    for field in mandatory_fields:
        if not (field in record and record[field]):
            print ' *', 'Missing field', field
            return False

    return True


def process_feed(feed):
    print ' *', 'processing', feed['url']

    rawxml = requests.get(feed['url'], headers=headers)
    d = feedparser.parse(rawxml.text)
    for entry in d['entries']:

        # standard fields:
        record = {
            "organization": feed['organization'],
            "link": get_entry_value(entry, 'link', feed),
            "title": get_entry_value(entry, 'title', feed),
            "date": get_entry_value(entry, 'published', feed),
            "user_tags": [],
            "description": "",
            "imgurl": ""
        }

        if 'category' in entry and entry['category']:
            record['user_tags'].append(get_entry_formatted("text/html", entry["category"]))

        if 'summary_detail' in entry and entry['summary_detail']:
            m = parse_content(entry["summary_detail"]["type"], entry["summary_detail"]["value"])
            if 'text' in m:
                record["description"] = m['text']
            if 'imgurl' in m:
                record["imgurl"] = m['imgurl']

        if 'media_thumbnail' in entry and entry['media_thumbnail']:
            media_thumbnail = entry['media_thumbnail'][0]
            if 'url' in media_thumbnail:
                record["imgurl"] = media_thumbnail['url']

        if 'tags' in entry and entry['tags']:
            for x in entry['tags']:
                if 'term' in x:
                    record['user_tags'].append(x['term'])

        record['user_tags'] = list(set(record['user_tags']))

        if not record['imgurl']:
            m = fetch_page_and_parse(feed, record['link'])
            for k in m:
                record[k] = m[k]

        if not validate(record):
            #print json.dumps(record, indent=True)
            #print '-'*60
            for k in entry:
                print k, '\t\t', entry[k]

            sys.exit(0)

        print record['imgurl']
        #print '-'*60


if __name__ == "__main__":

    with codecs.open('sources.json', 'rb', 'utf-8') as f:
        sources = json.loads(f.read().encode('utf-8'))

    try:
        for feed in sources['feeds']:
            if feed["organization"] == "Nowness":
                process_feed(feed)

    except Exception, e:
        traceback.print_exc()
        print str(e)
