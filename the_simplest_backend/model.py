import os
import json
import random
import yaml
import label_studio_sdk
import shutil as sh
from uuid import uuid4

import requests
import pandas as pd
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import get_single_tag_keys
from huggingface_hub.utils._errors import HfHubHTTPError
from ultralyticsplus import YOLO, download_from_hub, push_to_hfhub

LABEL_STUDIO_HOST = os.getenv("LABEL_STUDIO_HOST", "http://label_studio:8080")
LABEL_STUDIO_API_KEY = os.getenv(
    "LABEL_STUDIO_API_KEY", "ac5d1460f85bc9edd228ebbf08c6cf46f2361805"
)


def convert_xyxy(x, y, width, height, img_width, img_height):
    xmin = (x * img_width) / 100
    ymin = (y * img_height) / 100
    xmax = (width * img_width / 100) + xmin
    ymax = (height * img_height / 100) + ymin
    return xmin, ymin, xmax, ymax


def xyxy_to_xyxyn(bbox, image_width, image_height):
    """
    Convert bounding box coordinates from xyxy format to xyxyn format.

    Args:
        bbox (tuple): Bounding box coordinates in xyxy format (x_min, y_min, x_max, y_max).
        image_width (int): Width of the image.
        image_height (int): Height of the image.
        label (str): Label associated with the bounding box.

    Returns:
        tuple: Bounding box coordinates in xyxyn format (x_center, y_center, width, height, label).
    """
    x_min, y_min, x_max, y_max = bbox
    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    width = x_max - x_min
    height = y_max - y_min

    # Normalize coordinates
    x_center /= image_width
    y_center /= image_height
    width /= image_width
    height /= image_height

    return x_center, y_center, width, height


def load_data(data, label2id):
    image_id, x_center, y_center, width, height, classes = [], [], [], [], [], []
    for sample in data["annotation"]["result"]:
        image_id.append(data["task"]["data"]["image"])
        image_width = sample["original_width"]
        image_height = sample["original_height"]
        bbox = convert_xyxy(
            x=sample["value"]["x"],
            y=sample["value"]["y"],
            width=sample["value"]["width"],
            height=sample["value"]["height"],
            img_width=image_width,
            img_height=image_height,
        )
        bbox = xyxy_to_xyxyn(
            bbox=bbox, image_width=image_width, image_height=image_height
        )
        x_center.append(bbox[0])
        x_center.aapned(bbox[1])
        width.append(bbox[2])
        height.append(bbox[3])
        classes.append(label2id[sample["value"]["rectanglelabels"][0]])

    df = pd.DataFrame(
        {
            "image_id": image_id,
            "x_center": x_center,
            "y_center": y_center,
            "width": width,
            "height": height,
            "classes": classes,
        }
    )

    for image_id, mini in df.groupby("image_id"):
        row = (
            mini[["classes", "x_center", "y_center", "width", "height"]]
            .astype(str)
            .values
        )
        filename = image_id.split("/")[-1][:-4]
        if not os.path.exists("/tmp/train/labels"):
            os.makedirs("/tmp/train/labels")

        with open(f"/tmp/train/labels/{filename}.txt", "w") as f:
            for i in range(len(row)):
                text = " ".join(row[i])
                f.write(text)
                f.write("\n")

        if not os.path.exists("/content/train/images"):
            os.makedirs("/content/train/images")

        sh.copy(image_id, f"/content/train/images/{filename}.jpg")

    return True


class MyModel(LabelStudioMLBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        (
            self.from_name,
            self.to_name,
            self.value,
            self.labels_in_config,
        ) = get_single_tag_keys(self.parsed_label_config, "RectangleLabels", "Image")
        hf_model_id = os.getenv("HF_MODEL_ID", "linhcuem/checker_TB_yolov8_ver2")
        model_path = download_from_hub(hf_model_id)
        self.model = YOLO(model_path)

        # Path to the YAML file
        yaml_file_path = "/tmp/data.yaml"

        # Read the YAML file
        with open(yaml_file_path, "r") as yaml_file:
            data_yaml = yaml.safe_load(yaml_file)

        id2label = data_yaml["names"]
        self.label2id = {v: k for k, v in data_yaml["names"].items()}

    def predict(self, tasks, **kwargs):
        image_path = tasks[0]["data"][self.value]

        url = "http://bentoml:3000/annotation"
        payload = {}
        files = [
            ("", (image_path.split("/")[-1], open(image_path, "rb"), "image/jpeg"))
        ]
        headers = {"accept": "application/json"}
        response = requests.request(
            "POST", url, headers=headers, data=payload, files=files
        )
        json_response = json.loads(response.text)
        img_height = json_response["height"]
        img_width = json_response["width"]

        results = []
        all_scores = []
        for r in json_response["results"]:
            bbox = list(r["box"].values())
            if not bbox:
                continue
            score = float(r["confidence"])
            if score < 0.5:
                continue

            xmin, ymin, xmax, ymax = bbox
            results.append(
                {
                    "from_name": self.from_name,
                    "to_name": self.to_name,
                    "type": "rectanglelabels",
                    "value": {
                        "rectanglelabels": [r["name"]],
                        "x": xmin / img_width * 100,
                        "y": ymin / img_height * 100,
                        "width": (xmax - xmin) / img_width * 100,
                        "height": (ymax - ymin) / img_height * 100,
                    },
                    "score": score,
                }
            )
            all_scores.append(score)

        avg_score = sum(all_scores) / max(len(all_scores), 1)
        return [{"result": results, "score": avg_score}]

    def fit(self, event, data, **kwargs):
        """
        This method is called each time an annotation is created
         or updated
        It simply stores the latest annotation as a prediction
        model artifact"""
        # self.set("last_annotation", json.dumps(data["annotation"]["result"]))
        # to control the model versioning, you can use the model_version parameter
        # self.set("model_version", str(uuid4())[:8])
        ### Create dataset
        if load_data(data, self.label2id):
            ## Training Data
            print("training started")
            self.model.train(data="/tmp/data.yaml", epochs=2)
            hf_token = "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"
            if hf_token is None:
                raise ValueError(
                    "Please set HF_TOKEN environment variable to your HuggingFace token."
                )
            print("push to hub started")
            try:
                push_to_hfhub(
                    hf_model_id="chanelcolgate/chamdiemgianhang-test",
                    exp_dir="runs/detect/train",
                    hf_token=hf_token,
                    hf_private=False,
                    hf_dataset_id="chanelcolgate/yenthienviet",
                    thumbnail_text="YOLOv8s Cham diem gian hang Detection",
                )
                print("push to hub succeeded")
            except HfHubHTTPError as e:
                print("push to hub failed")
                print(e)

        print("error")
