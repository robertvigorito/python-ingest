import datetime
import glob
import logging
import os
import re
import alfred
import ffmpeg


import av

# from alfred import create

content_path = original_content_root = "/mnt/d/dh5"


content_path = content_path + "/*.MOV"
globbed_content = glob.glob(content_path, recursive=True)

project = "diego2"


def time_taken(func):
    def wrapper(*args, **kwargs):
        start = datetime.datetime.now()
        result = func(*args, **kwargs)
        end = datetime.datetime.now()
        print(f"Time taken: {round((end - start).total_seconds(), 3)}")
        return result

    return wrapper


@time_taken
def get_av_date(content: str) -> datetime:
    """Get the date of the content from the av package.

    Args:
        content (str): The path to the content.

    Returns:
        datetime: The date of the content.
    """

    inject_content_stream = av.open(content)

    # Get the date of the content
    created_time = inject_content_stream.metadata.get("creation_time")

    # Split the time
    date, time, *_ = created_time.split("T")
    # Remove the . from the time
    time = time.split(".")[0]

    content_date_time = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")

    # Create a datatime object

    return content_date_time


@time_taken
def get_ffprobe_date(content: str) -> datetime:
    """Get the date of the content from the ffprobe package.

    Args:
        content (str): The path to the content.

    Returns:
        datetime: The date of the content.
    """

    # Get the date of the content
    probe = ffmpeg.probe(content)
    created_time = probe["streams"][0]["tags"]["creation_time"]

    # Split the time
    date, time, *_ = created_time.split("T")
    # Remove the . from the time
    time = time.split(".")[0]

    content_date_time = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")

    # Create a datatime object

    return content_date_time


for ingest_content in globbed_content:

    av_date_time = get_av_date(ingest_content)

    # Get the year and the month as long name
    year = av_date_time.strftime("%Y")
    month = av_date_time.strftime("%B").lower()

    sequence = f"{month}_{year}"

    shot = os.path.basename(ingest_content).split(".")[0]

    print("Ingesting", project, sequence, shot)
    shot_context = alfred.context(project=project, sequence=sequence, shot=shot, comment="Ingested from Diego footage.")
