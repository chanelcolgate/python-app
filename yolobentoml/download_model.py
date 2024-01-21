from ultralyticsplus import YOLO, download_from_hub

model_path = download_from_hub("chanelcolgate/valorant-object-detection")
print(model_path)
model = YOLO(model_path)
