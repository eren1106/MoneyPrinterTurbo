import os
import streamlit as st
import sys
from uuid import uuid4
from loguru import logger
from app.services import llm

# Add the root directory of the project to the system path to allow importing modules
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.config import config
from app.models.schema import VideoParams
from app.services import task
from app.utils import utils

subscribe_script = "Subscribe now, and I’ll keep appearing to help you break the endless scrolling habit."

# Initialize session state variables if they don't exist
if 'stop_scrolling_script' not in st.session_state:
    st.session_state['stop_scrolling_script'] = "Hey—you’ve been scrolling for minutes, maybe even hours. What if you paused right now and used that time to learn something new, create, or move your body instead? Stop the endless feed: pick up a book, start a hobby, or go for a walk—make every moment count! " + subscribe_script

st.title("Stop Social Media")

with st.container(border=True):
    # Title field
    video_title = st.text_input(
        "Video Title",
        value="Stop Wasting Time on Social Media",
        help="Enter the title for your video"
    )

    # Caption field with regenerate button
    caption_col, btn_col = st.columns([4, 1])
    with caption_col:
        caption = st.text_area(
            "Script",
            value=st.session_state['stop_scrolling_script'],
            help="Enter the script for your video"
        )
    with btn_col:
        if st.button("🔄 Regenerate", key="regenerate_caption"):
            with st.spinner("Generating new script..."):
                new_caption = llm.generate_script(
                    video_subject="stop scrolling social media addiction",
                    paragraph_number=1
                )
                if "Error: " in new_caption:
                    st.error(new_caption)
                else:
                    st.session_state['stop_scrolling_script'] = new_caption + " " + subscribe_script
                    st.rerun()

    # Tags field
    # tags = st.text_input(
    #     "Tags",
    #     value="#fyp #productivity #procrastination #time management #success #motivation #discipline #AI",
    #     help="Enter tags separated by spaces"
    # )

    # Checkboxes
    col1, col2 = st.columns(2)
    with col1:
        use_hook = st.checkbox("Add Random Transitional Hook", value=True)
    with col2:
        upload_to_youtube = st.checkbox("Upload to YouTube", value=True)

    # Generate Video button
    start_button = st.button("Generate Video", use_container_width=True, type="primary")
    if start_button:
        config.save_config()
        task_id = str(uuid4())

        # Initialize video parameters
        params = VideoParams()
        params.video_subject = video_title
        params.use_transitional_hook = use_hook
        params.upload_to_youtube = upload_to_youtube

        # Set up logging
        log_container = st.empty()
        log_records = []

        def log_received(msg):
            if config.ui.get("hide_log", False):
                return
            with log_container:
                log_records.append(msg)
                st.code("\n".join(log_records))

        logger.add(log_received)

        st.toast("Generating Video")
        logger.info("Start Generating Video")
        logger.info(utils.to_json(params))

        # Start video generation
        result = task.start(task_id=task_id, params=params)
        if not result or "videos" not in result:
            st.error("Video Generation Failed")
            logger.error("Video Generation Failed")
            st.stop()

        video_files = result.get("videos", [])
        st.success("Video Generation Completed")

        # Display generated videos
        try:
            if video_files:
                player_cols = st.columns(len(video_files) * 2 + 1)
                for i, url in enumerate(video_files):
                    player_cols[i * 2 + 1].video(url)
        except Exception as e:
            logger.error(f"Error displaying videos: {str(e)}")

        logger.info("Video Generation Completed")
