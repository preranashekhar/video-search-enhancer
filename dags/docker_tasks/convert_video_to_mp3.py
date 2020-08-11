import youtube_dl
import os
from google.cloud import storage
import uuid


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

def convert_video_to_mp3():
    print("CONVERTING....")
    print("YOUTUBE_URL: ", os.getenv("YOUTUBE_URL"))

    audio_hash = str(uuid.uuid4())
    outtmpl = audio_hash + '.%(ext)s'

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([os.getenv("YOUTUBE_URL")])

    final_audio_file = 'audio_files/' + os.getenv("YOUTUBE_URL").split("=")[-1] + ":" + audio_hash + ".mp3"

    upload_blob("us-west3-video-enhancer-bb0ff304-bucket", audio_hash + ".mp3", final_audio_file)


print("START CONVERSION")
convert_video_to_mp3()
print("END CONVERSION")