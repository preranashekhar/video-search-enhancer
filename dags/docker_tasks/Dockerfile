FROM ubuntu

RUN apt-get update

RUN apt-get install -y ffmpeg

RUN apt install -y python3-pip

RUN pip3 install youtube_dl

RUN pip3 install google-cloud-storage

ADD convert_video_to_mp3.py /

ADD cmpe256.json /

CMD [ "python3", "/convert_video_to_mp3.py" ]