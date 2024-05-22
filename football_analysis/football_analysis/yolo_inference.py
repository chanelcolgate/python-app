# from ultralyticsplus import YOLO, download_from_hub

# hub_model_id = "chanelcolgate/football-analysis-v1"
# model_path = download_from_hub(hub_model_id)
# model = YOLO(model_path)

# results = model.predict(
#     "football_analysis/input_videos/08fd33_4.mp4", save=True
# )
# print(results[0])
# print("========================")
# for box in results[0].boxes:
#     print(box)

from roboflow import Roboflow
import supervision as sv
import numpy as np

from football_analysis.utils.video_utils import read_video, save_video


def annotate_predictions():
    rf = Roboflow(api_key="Bl39CGIjvJw5K0JYvQZl")
    project = rf.workspace().project("football-players-detection-3zvbc")
    model = project.version(9).model

    video_frames = read_video("football_analysis/input_videos/08fd33_4.mp4")
    frames = []
    for frame in video_frames:
        result = model.predict(frame, confidence=40, overlap=30).json()
        labels = [item["class"] for item in result["predictions"]]
        detections = sv.Detections.from_roboflow(result)
        label_annotator = sv.LabelAnnotator()
        box_annotator = sv.BoxAnnotator()

        annotated_image = box_annotator.annotate(
            scene=frame, detections=detections
        )
        annotated_image = label_annotator.annotate(
            scene=frame, detections=detections, labels=labels
        )
        frames.append(annotated_image)
        break

    save_video(frames, "football_analysis/output_videos/test.avi")


def count_predictions():
    rf = Roboflow(api_key="Bl39CGIjvJw5K0JYvQZl")
    project = rf.workspace().project("football-players-detection-3zvbc")
    model = project.version(9).model

    video_frames = read_video("football_analysis/input_videos/08fd33_4.mp4")
    for frame in video_frames:
        result = model.predict(frame, confidence=40).json()
        detections = sv.Detections.from_roboflow(result)

        print(len(detections))

        # Filter by class
        detections = detections[detections.class_id == 0]
        print(len(detections))
        break


def count_in_zone():
    rf = Roboflow(api_key="Bl39CGIjvJw5K0JYvQZl")
    project = rf.workspace().project("football-players-detection-3zvbc")
    model = project.version(9).model

    SOURCE_VIDEO_PATH = "football_analysis/input_videos/08fd33_4.mp4"
    TARGET_VIDEO_PATH = "football_analysis/output_videos/count_in_zone.avi"

    # use https://roboflow.github.io/polygonzone/ to get the points for your line
    polygon = np.array(
        [
            [422, 279],
            [1342, 231],
            [1906, 527],
            [1554, 883],
            [518, 883],
            [422, 276],
        ]
    )

    # create BYTETracker instance
    byte_tracker = sv.ByteTrack(
        track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30
    )

    # create VideoInfo instance
    video_info = sv.VideoInfo.from_video_path(SOURCE_VIDEO_PATH)
    # create frame generator
    generator = sv.get_video_frames_generator(SOURCE_VIDEO_PATH)
    # create PolygonZone instance
    zone = sv.PolygonZone(
        polygon=polygon,
        frame_resolution_wh=(video_info.width, video_info.height),
    )

    # create box annotator
    box_annotator = sv.BoxAnnotator(thickness=4, text_thickness=4, text_scale=2)

    colors = sv.ColorPalette.default()

    # create instance of BoxAnnotator
    zone_annotator = sv.PolygonZoneAnnotator(
        thickness=4,
        text_thickness=4,
        text_scale=2,
        zone=zone,
        color=colors.colors[0],
    )

    # define call back function to be used in video processing
    def callback(frame: np.ndarray, index: int) -> np.ndarray:
        # model prediction on single frame and conversion to supervision Detection
        # with tempfile.NamedTemporaryFile(suff?ix=".jpg") as temp:
        results = model.predict(frame).json()

        detections = sv.Detections.from_roboflow(results)
        zone.trigger(detections=detections)

        # show detections in real time
        # print(detections)

        # tracking detections
        detections_supervision = byte_tracker.update_with_detections(detections)
        labels = {0: "ball", 1: "goalkeeper", 2: "player", 3: "referee"}

        labels_convert = [
            f"#{tracker_id} {labels[class_id]} {confidence:0.2f}"
            for _, _, confidence, class_id, tracker_id, _ in detections_supervision
        ]

        annotated_frame = box_annotator.annotate(
            scene=frame,
            detections=detections_supervision,
            labels=labels_convert,
        )
        annotated_frame = zone_annotator.annotate(scene=annotated_frame)
        # return frame with box and line annotated result
        return annotated_frame

    # process the whole video
    sv.process_video(
        source_path=SOURCE_VIDEO_PATH,
        target_path=TARGET_VIDEO_PATH,
        callback=callback,
    )


def count_across_line():
    rf = Roboflow(api_key="Bl39CGIjvJw5K0JYvQZl")
    project = rf.workspace().project("football-players-detection-3zvbc")
    model = project.version(9).model

    SOURCE_VIDEO_PATH = "football_analysis/input_videos/08fd33_4.mp4"
    TARGET_VIDEO_PATH = "football_analysis/output_videos/count_across_line.avi"

    # use https://roboflow.github.io/polygonzone/ to get the points for your line
    LINE_START = sv.Point(426, 270)
    LINE_END = sv.Point(526, 1000)

    # create BYTETracker instance
    byte_tracker = sv.ByteTrack(
        track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30
    )

    # create VideoInfo instance
    video_info = sv.VideoInfo.from_video_path(SOURCE_VIDEO_PATH)

    # create frame generator
    generator = sv.get_video_frames_generator(SOURCE_VIDEO_PATH)

    # create LineZone instance, it is perviously called LineCounter class
    line_zone = sv.LineZone(start=LINE_START, end=LINE_END)

    # create instance of BoxAnnotator
    box_annotator = sv.BoxAnnotator(thickness=4, text_thickness=4, text_scale=2)

    # create instance of TraceAnnotator
    trace_annotator = sv.TraceAnnotator(thickness=4, trace_length=50)
    line_zone_annotator = sv.LineZoneAnnotator(
        thickness=4, text_thickness=4, text_scale=2
    )

    # define call back function to be used in video processing
    def callback(frame: np.ndarray, index: int) -> np.ndarray:
        # model prediction on single frame and conversion to supervision Detections
        # with tempfile.NamedTemporaryFile(suff?ix=".jpg") as temp:
        results = model.predict(frame).json()

        detections = sv.Detections.from_roboflow(results)

        # show detections in real time
        # print(detections)

        # tracking detections
        detections_supervision = byte_tracker.update_with_detections(detections)
        labels = {0: "ball", 1: "goalkeeper", 2: "player", 3: "referee"}
        labels_convert = [
            f"#{tracker_id} {labels[class_id]} {confidence:0.2f}"
            for _, _, confidence, class_id, tracker_id, _ in detections_supervision
        ]

        annotated_frame = trace_annotator.annotate(
            scene=frame.copy(),
            detections=detections_supervision,
        )
        annotated_frame = box_annotator.annotate(
            scene=annotated_frame,
            detections=detections_supervision,
            labels=labels_convert,
        )

        # update line counter
        line_zone.trigger(detections_supervision)
        # return frame with box and line annotated result
        return line_zone_annotator.annotate(
            annotated_frame, line_counter=line_zone
        )

    # process the whole video
    sv.process_video(
        source_path=SOURCE_VIDEO_PATH,
        target_path=TARGET_VIDEO_PATH,
        callback=callback,
    )
