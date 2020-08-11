import datetime
import os
from collections import defaultdict
import json


import airflow
from airflow.contrib.operators import kubernetes_pod_operator
from airflow.operators.python_operator import PythonOperator
from google.cloud import storage
from google.cloud import speech_v1

from algoliasearch.search_client import SearchClient

YESTERDAY = datetime.datetime.now() - datetime.timedelta(days=1)

BUCKET_NAME = "us-west3-video-enhancer-bb0ff304-bucket"

def _get_latest_audio_file():
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    all_blobs = list(client.list_blobs(bucket, prefix="audio_files/"))
    for blob in all_blobs:
        print("blob name: ", blob.name)

    print("all_blobs[-1].name.split('/')[1]: ", all_blobs[-1].name.split('/')[1])

    return all_blobs[-1].name.split('/')[1]


def index_speech_to_search(**context):
    print("context: ", context)
    json_to_index = context['task_instance'].xcom_pull(task_ids='convert_mp3_to_speech')

    print("json_to_index: ", json_to_index)

    client = SearchClient.create(os.getenv("ALGOLIA_APP_ID"), os.getenv("ALGOLIA_SECRET_KEY"))
    index = client.init_index('videos')

    print("index: ", index)
    index.save_object(json.loads(json_to_index), {'autoGenerateObjectIDIfNotExist': True})


def convert_mp3_to_speech():
    latest_audio_file = _get_latest_audio_file()
    print("latest_audio_file: ", latest_audio_file)
    storage_uri = "gs://us-west3-video-enhancer-bb0ff304-bucket/audio_files/" + latest_audio_file

    print("storage_uri: ", storage_uri)

    client = speech_v1.SpeechClient()
    enable_word_time_offsets = True

    sample_rate_hertz = 48000
    language_code = "en-US"

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    # encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    config = {
        "sample_rate_hertz": sample_rate_hertz,
        "language_code": language_code,
        "enable_word_time_offsets": enable_word_time_offsets
    }
    audio = {"uri": storage_uri}

    operation = client.long_running_recognize(config, audio)

    print("Waiting for operation to complete...")
    response = operation.result()

    response_dict = {
        "transcript": "",
        "word_timestamps": defaultdict(list),
        "video_url": YOUTUBE_URL
    }
    print("response from SpeechToText", response.results)

    verbose = False

    for result in response.results:
        alternative = result.alternatives[0]
        response_dict["transcript"] += alternative.transcript

        for word in alternative.words:
            response_dict["word_timestamps"][word.word.lower()].append(word.start_time.seconds)

            if verbose:
                print(u"Word: {}".format(word.word))

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

    json_data_for_search_indexing = json.dumps(response_dict)
    print("json_data_for_search_indexing: ", json_data_for_search_indexing)

    return json_data_for_search_indexing


default_args = {
    'owner': 'Video Enhancer',
    'depends_on_past': False,
    'email': ['prerana.shekhar.07@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=5),
    'start_date': YESTERDAY,
}


YOUTUBE_URL='https://www.youtube.com/watch?v=OyQCz_gUwIY'

with airflow.DAG(
    'video_enhancer',
    'catchup=False',
    default_args=default_args,
    schedule_interval=datetime.timedelta(days=1)) as dag:

    task_convert_video_to_mp3 = kubernetes_pod_operator.KubernetesPodOperator(
        task_id='convert_video_to_mp3',
        name='convert-video-to-mp3',
        namespace='default',
        image='gcr.io/cmpe256-279717/convert_video_to_mp3',
        env_vars={'YOUTUBE_URL': YOUTUBE_URL,
            'GOOGLE_APPLICATION_CREDENTIALS': '/cmpe256.json'
        }
    )

    task_convert_mp3_to_speech = PythonOperator(
        task_id='convert_mp3_to_speech',
        python_callable=convert_mp3_to_speech
    )

    task_index_speech_to_search = PythonOperator(
        task_id='index_speech_to_search',
        python_callable=index_speech_to_search,
        provide_context=True
    )

    task_convert_video_to_mp3 >> task_convert_mp3_to_speech >> task_index_speech_to_search
