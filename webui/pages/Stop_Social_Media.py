import os
import streamlit as st
import sys
from uuid import uuid4
from loguru import logger

# Add the root directory of the project to the system path to allow importing modules
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.config import config
from app.models.schema import VideoParams
from app.services import task as tm
from app.utils import utils

# Initialize session state variables if they don't exist
if 'stop_social_caption' not in st.session_state:
    st.session_state['stop_social_caption'] = "Stop scrolling endlessly! 🛑 Take control of your life and break free from social media addiction. Your time is precious - make it count! 🌟 #DigitalWellness #Mindfulness"

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
            "Caption",
            value=st.session_state['stop_social_caption'],
            help="Enter the caption for your video"
        )
    with btn_col:
        if st.button("🔄 Regenerate", key="regenerate_caption"):
            # Here you would typically call your caption generation logic
            # For now, we'll just use a simple alternative
            new_caption = "Break free from social media addiction! 🎯 Start living in the present moment and rediscover what truly matters. Your life is waiting! ✨ #DigitalDetox #Mindfulness"
            st.session_state['stop_social_caption'] = new_caption
            st.rerun()

    # Tags field
    tags = st.text_input(
        "Tags",
        value="#StopSocialMedia #DigitalWellness #Mindfulness #DigitalDetox #Productivity",
        help="Enter tags separated by spaces"
    )

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
        result = tm.start(task_id=task_id, params=params)
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
