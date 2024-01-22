import json
from typing import Dict, Any
from collections import Counter

import bentoml
import torch
import PIL
from bentoml.io import Image
from bentoml.io import JSON


class Yolov8Runnable(bentoml.Runnable):
    SUPPORTED_RESOURCES = ("nvidia.com/gpu", "cpu")
    SUPPORTS_CPU_MULTI_THREADING = True

    def __init__(self):
        from ultralyticsplus import YOLO, download_from_hub

        model_path = download_from_hub("chanelcolgate/valorant-object-detection")
        self.model = YOLO(model_path)

        if torch.cuda.is_available():
            self.model.cuda()
        else:
            self.model.cpu()

        # Config inference settings
        self.inference_size = 416

        # Optional configs
        self.model.overrides["conf"] = 0.5  # NMS confidence threshold
        self.model.overrides["iou"] = 0.45  # NMS IoU threshold
        self.model.overrides["agnostic_nms"] = False
        self.model.overrides["max_det"] = 1000

    @bentoml.Runnable.method(batchable=False, batch_dim=0)
    def inference(self, input_imgs):
        # Return predictions only
        results = self.model(input_imgs)
        result = results[0]
        json_result = json.loads(result.tojson())
        class_counts = Counter(detection["name"] for detection in json_result)
        return class_counts

    @bentoml.Runnable.method(batchable=False, batch_dim=0)
    def render(self, input_imgs):
        # Return images with boxes and labels
        results = self.model(input_imgs)
        result = results[0]
        im_array = result.plot()
        im = PIL.Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.save("images/results.jpg")  # save image

        json_result = json.loads(result.tojson())
        class_counts = Counter(detection["name"] for detection in json_result)
        return class_counts

    @bentoml.Runnable.method(batchable=False, batch_dim=0)
    def annotation(self, input_imgs):
        results = self.model(input_imgs)
        result = results[0]
        json_results = json.loads(result.tojson())
        height, width = result.orig_shape
        return {"height": height, "width": width, "results": json_results}


yolo_v8_runner = bentoml.Runner(Yolov8Runnable, max_batch_size=30)

svc = bentoml.Service("yolo_v8_demo", runners=[yolo_v8_runner])


@svc.api(input=Image(), output=JSON())
async def invocation(input_img):
    batch_ret = await yolo_v8_runner.inference.async_run(input_img)
    return batch_ret


@svc.api(input=Image(), output=JSON())
async def render(input_img):
    batch_ret = await yolo_v8_runner.render.async_run(input_img)
    return batch_ret


@svc.api(input=Image(), output=JSON())
async def annotation(input_img):
    batch_ret = await yolo_v8_runner.annotation.async_run(input_img)
    return batch_ret
