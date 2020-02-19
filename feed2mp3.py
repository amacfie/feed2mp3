import os
import random
import re
import tempfile

from goose3 import Goose
from pydub import AudioSegment
import argparse
import feedparser
import nltk
import unidecode

# http://www.overcomingbias.com/feed
parser = argparse.ArgumentParser(
        description='''
        Download blog posts as mp3 files using Google Text-to-Speech API.''')
parser.add_argument('num_entries', help='Number of posts to download')
parser.add_argument('feed_url', help='URL of RSS/atom feed')

args = parser.parse_args()
feed_url = args.feed_url
num_entries = int(args.num_entries)

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unidecode.unidecode(value)
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return value

def cloud_tts(text, fn):
    '''Synthesizes speech from the input string of text.'''
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.types.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(
        name='en-US-Wavenet-F',
        language_code='en-US')

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    with open(fn, 'wb') as out:
        out.write(response.audio_content)

# https://cloud.google.com/text-to-speech/quotas
def call_tts(text, filename):
    sentences = nltk.sent_tokenize(text)
    chunks = ['']
    for sentence in sentences:
        candidate_chunk = chunks[-1] + ' ' + sentence
        if len(candidate_chunk) < 5000:
            chunks[-1] = candidate_chunk
        else:
            chunks.append(sentence)
    fn_base = str(random.randint(1, 10000))
    segments = []
    for i, chunk in enumerate(chunks):
        print('Processing chunk...')
        fn = os.path.join(
                tempfile.gettempdir(), '{0}_{1}.mp3'.format(fn_base, i))
        cloud_tts(chunk, fn)
        segments.append(AudioSegment.from_mp3(fn))

    sum(segments).export(filename, format='mp3')


g = Goose({'parser_class': 'soup'})
d = feedparser.parse(feed_url)

print('Converting ' + d.feed.title + '...')

entries_count = 0
for entry in d.entries:
    # get date field (y m d)
    entry_date = ' '.join(str(x) for x in entry.published_parsed[0:3])
    # get title field
    entry_title = entry.title
    print('  Converting "' + entry_title + '"...')
    # create slugified filename
    entry_name = slugify(entry_date + '_' + entry_title)
    filename = entry_name + '.mp3'
    # if the feed contains the content, use that; otherwise use the URL
    if 'content' in entry:
        content_text = g.extract(
            raw_html=entry.content[0]['value']).cleaned_text
    else:
        content_text = g.extract(url=entry['link']).cleaned_text
    # use Google text-to-speech to convert from text to mp3 file
    print('  Saving to ' + filename + '...')
    call_tts(content_text, filename)
    entries_count += 1
    if entries_count == num_entries:
        break

