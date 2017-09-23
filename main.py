# ex. http://www.overcomingbias.com/feed

from bs4 import BeautifulSoup
from functional import seq
from gtts import gTTS
import codecs
import feedparser
import html
import re
import unidecode

def clean_xml(xml):
    # parse xml
    soup = BeautifulSoup(xml, 'lxml')
    # extract text
    text = soup.getText(separator=' ')
    # remove/convert improper characters
    text = html.unescape(text)
    text = re.sub('(>|\\[|\\])', ' ', text)
    text = unidecode.unidecode(text)
    text = re.sub(r'\s+', ' ', text)
    return text

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unidecode.unidecode(value)
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return value

d = feedparser.parse('http://www.overcomingbias.com/feed')

print('Converting ' + d.feed.title + '...')

for entry in d.entries:
    entry_date = '_'.join(str(x) for x in entry.published_parsed[0:3])
    entry_title = entry.title
    print('  Converting "' + entry_title + '"...')
    entry_name = entry_date + '-' + entry_title
    filename = slugify(entry_name) + '.mp3'

    content_text = clean_xml(entry.content[0]['value'])
    print('  Saving to ' + filename + '...')
    tts = gTTS(text=content_text, lang='en')
    #tts.save(filename)
    print(content_text)  # JFT

