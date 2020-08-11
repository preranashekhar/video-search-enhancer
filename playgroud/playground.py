from __future__ import unicode_literals
import youtube_dl

ydl_opts = {
    # 'format': 'bestaudio/best'
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=_dfLOzuIg2o'])

import os
from google.cloud import speech_v1
from collections import defaultdict
import json

print(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

def sample_long_running_recognize(storage_uri):
    """
    Transcribe long audio file from Cloud Storage using asynchronous speech
    recognition

    Args:
      storage_uri URI for audio file in Cloud Storage, e.g. gs://[BUCKET]/[FILE]
    """

    client = speech_v1.SpeechClient()
    enable_word_time_offsets = True

    # storage_uri = 'gs://cloud-samples-data/speech/brooklyn_bridge.raw'

    # Sample rate in Hertz of the audio data sent
    # sample_rate_hertz = 16000
    sample_rate_hertz = 48000
    # The language of the supplied audio
    language_code = "en-US"

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    # encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    config = {
        "sample_rate_hertz": sample_rate_hertz,
        "language_code": language_code,
        "enable_word_time_offsets": enable_word_time_offsets
        # "encoding": encoding,
    }
    audio = {"uri": storage_uri}

    operation = client.long_running_recognize(config, audio)

    print(u"Waiting for operation to complete...")
    response = operation.result()

    response_dict = {
        "transcript": "",
        "word_timestamps": defaultdict(list),
        "video_url": "https://www.youtube.com/watch?v=PqMGmRhKsnM"
    }
    print("response", response.results)

    for result in response.results:
        alternative = result.alternatives[0]
        response_dict["transcript"] += alternative.transcript

        print(u"Transcript: {}".format(alternative.transcript))
        # Print the start and end time of each word
        for word in alternative.words:
            print(u"Word: {}".format(word.word))
            response_dict["word_timestamps"][word.word.lower()].append(word.start_time.seconds)

            print(
                u"Start time: {} seconds {} nanos".format(
                    word.start_time.seconds, word.start_time.nanos
                )
            )
            print(
                u"End time: {} seconds {} nanos".format(
                    word.end_time.seconds, word.end_time.nanos
                )
            )

    print(json.dumps(response_dict))

# path = '/Users/prerana/projects/video-search-enhancer/audio_test.mp3'
uri = 'gs://video_enhancer/docker.mp3'
sample_long_running_recognize(uri)