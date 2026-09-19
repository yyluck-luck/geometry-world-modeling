def save_video(video, path, fps=10):
    video = video.permute(0, 2, 3, 1)
    video_codec = "libx264"
    video_options = {
        "crf": "23",  # Constant Rate Factor (lower value = higher quality, 18 is a good balance)
        "preset": "slow",
    }
    write_video(str(path), video, fps=fps, video_codec=video_codec, options=video_options)
