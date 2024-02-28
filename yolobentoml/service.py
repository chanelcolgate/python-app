import base64
import hashlib
import secrets
import json
import os
import platform
from typing import Dict, Any
from collections import Counter

import bentoml
import torch
import PIL
import imagehash
from bentoml.io import Image
from bentoml.io import JSON


class Yolov8Runnable(bentoml.Runnable):
    SUPPORTED_RESOURCES = ("nvidia.com/gpu", "cpu")
    SUPPORTS_CPU_MULTI_THREADING = True

    def __init__(self):
        from ultralyticsplus import YOLO, download_from_hub

        hf_model_id = os.getenv("HF_MODEL_ID", "linhcuem/checker_TB_yolov8_ver2")

        model_path = download_from_hub(hf_model_id)
        self.model = YOLO(model_path)

        if torch.cuda.is_available():
            self.model.cuda()
        else:
            self.model.cpu()

        # Config inference settings
        self.inference_size = 640

        # Optional configs
        # self.model.overrides["conf"] = 0.5  # NMS confidence threshold
        # self.model.overrides["iou"] = 0.45  # NMS IoU threshold
        # self.model.overrides["agnostic_nms"] = False
        # self.model.overrides["max_det"] = 1000
        self.model.conf = os.getenv("MODEL_CONF", 0.5)
        self.model.iou = os.getenv("MODEL_IOU", 0.45)

        self.operating_system = platform.system()

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
        h = hashlib.sha1()
        h.update(str(imagehash.phash(input_imgs)).encode("utf-8"))
        filename = f"{h.hexdigest()}.jpg"
        if self.operating_system == "Windows":
            filename = f"C:\\Users\\NGUYEN~1\\AppData\\Local\\Temp\{filename}"
        else:
            if not os.path.exists("/tmp/images"):
                os.makedirs("/tmp/images")
            filename = f"/tmp/images/{filename}"

        # Return images with boxes and labels
        results = self.model(input_imgs)
        result = results[0]
        im_array = result.plot()
        im = PIL.Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.save(filename)  # save image

        json_result = json.loads(result.tojson())
        class_counts = Counter(detection["name"] for detection in json_result)
        return class_counts, filename

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
