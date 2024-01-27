import json
from collections import Counter

from ultralyticsplus import YOLO, download_from_hub

model_path = download_from_hub("linhcuem/checker_TB_yolov8_ver2")
print(model_path)
model = YOLO(model_path)
results = model(["_G3500373_1704689029839.jpg", "_G3500478_1704875778034.jpg"])
for result in results:
    json_result = json.loads(result.tojson())
    class_counts = Counter(detection["name"] for detection in json_result)
    print(class_counts)
