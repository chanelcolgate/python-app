import cv2

from football_analysis.utils.video_utils import read_video, save_video
from football_analysis.trackers.tracker import Tracker


def main():
    # Read Video
    video_frames = read_video("football_analysis/input_videos/08fd33_4.mp4")

    # Initialize tracker
    tracker = Tracker("chanelcolgate/football-analysis-v1")

    tracks = tracker.get_object_tracks(
        video_frames,
        read_from_stub=True,
        stub_path="football_analysis/stubs/track_stubs.pkl",
    )

    # save cropped image of a player
    for track_id, player in tracks["players"][0].items():
        bbox = player["bbox"]
        frame = video_frames[0]

        # crop bbox from frame
        cropped_image = frame[
            int(bbox[1]) : int(bbox[3]), int(bbox[0]) : int(bbox[2])
        ]

        # save the cropped image
        cv2.imwrite(
            f"football_analysis/output_videos/cropped_img.jpg", cropped_image
        )
        break

    # Draw
    ## Draw object Tracks
    output_video_frames = tracker.draw_annotations(video_frames, tracks)

    # Save Video
    save_video(
        output_video_frames, "football_analysis/output_videos/output_video.avi"
    )


if __name__ == "__main__":
    main()
