import glob

import cv2

from football_analysis.utils.video_utils import read_video, save_video
from football_analysis.trackers.tracker import Tracker
from football_analysis.team_assigner.team_assigner import TeamAssigner


def main():
    # Read Video
    frames = []
    for image_path in glob.glob("football_analysis/input_videos/video3/*.jpg"):
        frame = cv2.imread(image_path)
        frames.append(frame)

    # Save Video
    save_video(frames, "football_analysis/output_videos/video3.avi")


def main_1():
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
    # for track_id, player in tracks["players"][0].items():
    #     bbox = player["bbox"]
    #     frame = video_frames[0]

    #     # crop bbox from frame
    #     cropped_image = frame[
    #         int(bbox[1]) : int(bbox[3]), int(bbox[0]) : int(bbox[2])
    #     ]

    #     # save the cropped image
    #     cv2.imwrite(
    #         f"football_analysis/output_videos/cropped_img.jpg", cropped_image
    #     )
    #     break

    # Assigner Player Teams
    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks["players"][0])

    for frame_num, player_track in enumerate(tracks["players"]):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(
                video_frames[frame_num], track["bbox"], player_id
            )
            tracks["players"][frame_num][player_id]["team"] = team
            tracks["players"][frame_num][player_id]["team_color"] = (
                team_assigner.team_colors[team]
            )
    # Draw
    ## Draw object Tracks
    output_video_frames = tracker.draw_annotations(video_frames, tracks)

    # Save Video
    save_video(
        output_video_frames, "football_analysis/output_videos/output_video.avi"
    )


if __name__ == "__main__":
    main()
