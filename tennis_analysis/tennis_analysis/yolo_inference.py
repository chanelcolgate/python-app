# from ultralytics import YOLO

# model = YOLO("yolov8x")
# model.predict("tennis_analysis/input_videos/input_video.mp4", save=True)

from ultralyticsplus import YOLO, download_from_hub

hub_model_id = "chanelcolgate/tennis-analysis-v1"
model_path = download_from_hub(hub_model_id)
model = YOLO(model_path)

results = model.predict(
    "tennis_analysis/input_videos/input_video.mp4", save=True
)
