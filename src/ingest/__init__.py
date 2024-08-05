"""Ingest content for the wgid pipeline.

TODO:
- [] Create a prores ingest 
- [] Create a h264 ingest
- [] Create shot from that ingested plate
- [] Update the entrees to the database


"""
import glob
import logging
import os
import re
import ffmpeg

# from alfred import create

content_path = original_content_root = "/mnt/d/dh5"




content_path = content_path + "/*.MOV"
globbed_content = glob.glob(content_path, recursive=True)


# Convert the content to prores

prores_high_loseless = dict(vcodec='prores_ks', profile='2', threads=28,  preset='ultrafast')

# ffmpeg -i input.mov -pix_fmt rgb48le output_%04d.exr
exr_16b = {
    "pix_fmt": "rgb48le",
    "vcodec": "exr",
}

dnxhd = {
    "vcodec": "dnxhd",
    "profile:v": "dnxhr_hq",
    "b:v": "36M",
    "pix_fmt": "yuv422p",
    "threads": 28,
    # "preset": "ultrafast",
}

job = "diego"
sequence = "001"


import alfred
from alfred.models import assets


release_items = []

for ingest_content in globbed_content:
    shot_code_results = re.findall(r"([a-zA-Z]+)([\d]+)", os.path.basename(ingest_content))
    if not shot_code_results:
        continue
    # Create the shot context and the ingest asset entree
    shot = "_".join(shot_code_results[0])
    shot_context = alfred.context(
        project=job,
        sequence=sequence,
        shot=shot,
        comment="Ingested from Diego footage."
    )
    if shot_context is None:
        logging.warning(f"Shot context {shot_context} does not exist.")
        continue
    # Create thumbnail of the image
    ingested_video_asset = assets.Asset(
        context=shot_context,
        name="mp01",
        type_="plate",
    )
    release_items.append(ingested_video_asset)
    root_path, extension = os.path.splitext(ingest_content)
    prores_output_path = f"{root_path}.%04d.exr"
    
    # Check that paths are not the same
    if prores_output_path == ingest_content:
        raise ValueError("Prores output path is the same as the ingest content.")
    
    # Bulk release the constructed assets and generate the thumbnail
    # Having a URL object would be nice!


    print("here")
    prores_output_path = f"{root_path}_dnxhd.mov"

    stream = ffmpeg.input(ingest_content)
    stream = ffmpeg.output(stream, prores_output_path, **dnxhd)
    stream = ffmpeg.overwrite_output(stream=stream)
    # Subpress the stdout
    # ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    ingested_video_asset.inject(prores_output_path, key="primary")

    # Create exrs from the content



from alfred._core.controller import ReleaseModels



ReleaseModels(release_items).release()



    





