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

one_day = 60 * 60 * 24
requests_cache.install_cache(
    'rss_cache', backend='sqlite', expire_after=one_day)

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
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html5lib')
    result = {}

    if 'find_image_selector' in feed:
        for el in soup.findAll(feed['find_image_selector']['element'], {"class": feed['find_image_selector']['class']}):
            for img in el.findAll('img'):
                if img['src'].startswith('/'):
                    result['imgurl'] = feed['find_image_selector']['root'] + img['src']
                else:
                    result['imgurl'] = img['src']
                break
    else:
        # look for og_image as the default
        if soup.find('meta', {"property": "og:image"}):
            if 'content' in soup.find('meta', {"property": "og:image"}):
                result['imgurl'] = soup.find('meta', {"property": "og:image"})['content']


def process_feed(feed):
    rawxml = requests.get(feed['url'])
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
            record["description_snippet"] = m['text']
            if 'imgurl' in m:
                record['imgurl'] = m['imgurl']

        if 'content' in entry and entry['content']:
            m = parse_content(entry["content"][0]["type"], entry["content"][0]["value"])
            record["description"] = m['text']
            if 'imgurl' in m:
                record['imgurl'] = m['imgurl']

        if 'media_content' in entry and entry['media_content'][0]['type'] == 'image/jpeg':
            record['imgurl'] = entry['media_content'][0]['url']

        if 'tags' in entry and entry['tags']:
            for x in entry['tags']:
                if 'term' in x:
                    record['user_tags'].append(x['term'])

        record['user_tags'] = list(set(record['user_tags']))

        if 'replacement' in feed:
            for k in feed['replacement']:
                record[k] = feed['replacement'][k][0] % (record[feed['replacement'][k][1]])
                record[feed['replacement'][k][1]] = ""


        if not record['imgurl']:
            print json.dumps(record, indent=True)
            m = fetch_page_and_parse(feed, record['link'])
            for k in m:
                record[k] = m[k]


        #print record['imgurl']
        #print '-'*60


if __name__ == "__main__":

    with codecs.open('sources.json', 'rb', 'utf-8') as f:
        sources = json.loads(f.read().encode('utf-8'))

    try:
        for feed in sources['feeds']:
            process_feed(feed)

    except Exception, e:
        traceback.print_exc()
        print str(e)
