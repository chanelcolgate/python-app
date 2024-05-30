import glob

import cv2
import numpy as np

from football_analysis.utils.video_utils import read_video, save_video
from football_analysis.trackers.tracker import Tracker
from football_analysis.team_assigner.team_assigner import TeamAssigner
from football_analysis.player_ball_assigner.player_ball_assigner import (
    PlayerBallAssigner,
)
from football_analysis.camera_movement_estimator.camera_movement_estimator import (
    CameraMovementEstimator,
)
from football_analysis.view_transformer.view_transformer import ViewTransformer
from football_analysis.speed_and_distance_estimator.speed_and_distance_estimator import (
    SpeedAndDistance_Estimator,
)


# def main():
#     # Read Video
#     frames = []
#     for image_path in glob.glob("football_analysis/input_videos/video3/*.jpg"):
#         frame = cv2.imread(image_path)
#         frames.append(frame)

#     # Save Video
#     save_video(frames, "football_analysis/output_videos/video3.avi")


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
    # Get object positions
    tracker.add_position_to_track(tracks)

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

    # Camera Movement Estimator
    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(
        video_frames,
        read_from_stub=True,
        stub_path="football_analysis/stubs/camera_movement.pkl",
    )
    camera_movement_estimator.add_adjust_positions_to_tracks(
        tracks, camera_movement_per_frame
    )

    # View Transformer
    view_transformer = ViewTransformer()
    view_transformer.add_transformed_position_to_track(tracks)

    # Speed and distance estimator
    speed_and_distance_estimator = SpeedAndDistance_Estimator()
    speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)

    # Interpolate Ball Positions
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

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
    # Assign Ball Aquisition
    player_assigner = PlayerBallAssigner()
    team_ball_control = []
    for frame_num, player_track in enumerate(tracks["players"]):
        ball_bbox = tracks["ball"][frame_num][1]["bbox"]
        assigner_player = player_assigner.assign_ball_to_player(
            player_track, ball_bbox
        )

        if assigner_player != -1:
            tracks["players"][frame_num][assigner_player]["has_ball"] = True
            team_ball_control.append(
                tracks["players"][frame_num][assigner_player]["team"]
            )
        else:
            team_ball_control.append(team_ball_control[-1])

    team_ball_control = np.array(team_ball_control)

    # Draw Output
    ## Draw object Tracks
    output_video_frames = tracker.draw_annotations(
        video_frames, tracks, team_ball_control
    )

    ## Draw Camera Movement
    output_video_frames = camera_movement_estimator.draw_camera_movement(
        output_video_frames, camera_movement_per_frame
    )

    ## Draw Speed and Distance
    output_video_frames = speed_and_distance_estimator.draw_speed_and_distance(
        output_video_frames, tracks
    )

    # Save Video
    save_video(
        output_video_frames, "football_analysis/output_videos/output_video.avi"
    )


if __name__ == "__main__":
    main()
