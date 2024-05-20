from ultralyticsplus import YOLO, download_from_hub

hub_model_id = "chanelcolgate/football-analysis-v1"
model_path = download_from_hub(hub_model_id)
model = YOLO(model_path)

results = model.predict(
    "football_analysis/input_videos/08fd33_4.mp4", save=True
)
print(results[0])
print("========================")
for box in results[0].boxes:
    print(box)
