### Setup
```
!pip install -q huggingface_hub ultralyticsplus
!huggingface-cli login
import ultralytics
ultralytics.checks()
```
### Download Data
```
!pip install -q roboflow

from roboflow import Roboflow
rf = Roboflow(api_key="Bl39CGIjvJw5K0JYvQZl")
project = rf.workspace("daniels-magonis-0pjzx").project("valorant-9ufcp")
dataset = project.version(1).download("yolov8")
```
### Create data.yaml
```
yaml_text = """names:
- dropped spike
- enemy
- planted spike
- teammate
nc: 4
roboflow:
  license: CC BY 4.0
  project: valorant-9ufcp
  url: https://universe.roboflow.com/daniels-magonis-0pjzx/valorant-9ufcp/dataset/1
  version: 1
  workspace: daniels-magonis-0pjzx
test: ../test/images
train: /content/valorant-1/train/images
val: /content/valorant-1/valid/images"""
```
### Write file data.yaml
```
with open("data.yaml", 'w') as f:
    f.write(yaml_text)
%cat data.yaml
```
### Train data
```
!yolo train model=yolov8m.pt data=data.yaml epochs=3 imgsz=416
```
### Push to hub
```
!ultralyticsplus --exp_dir runs/detect/train --hf_model_id chanelcolgate/valorant-object-detection
```
### Load to hub
```
#@title #### load to hub
from ultralyticsplus import (
    YOLO,
    download_from_hub,
    postprocess_classify_output,
    render_result,
    push_to_hfhub,
)

# load model
# model = YOLO('chanelcolgate/valorant-object-detection')
model_path = download_from_hub('chanelcolgate/valorant-object-detection')
model = YOLO(model_path)

# set model parameters
model.overrides['conf'] = 0.25  # NMS confidence threshold
model.overrides['iou'] = 0.45  # NMS IoU threshold
model.overrides['agnostic_nms'] = False  # NMS class-agnostic
model.overrides['max_det'] = 1000  # maximum number of detections per image

# set image
image = 'https://transform.roboflow.com/J6YLfA0RLPhDyMbKbQPiq2jlqsF3/1f3cb095363002e0dc53e59a736e4922/thumb.jpg'

# perform inference
results = model.predict(image, imgsz=416)

# parse results
result = results[0]
boxes = result.boxes.xyxy
scores =result.boxes.conf
categories = result.boxes.cls
# scores = result.probs # for classification models
# masks = result.masks # for segmentation models

# show results on image
render = render_result(model=model, image=image, result=result)
render.show()
```
