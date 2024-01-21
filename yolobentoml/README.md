## Install dependencies
Create a `requirements.txt` file that contains the following packages:
```
bentoml==1.1.11
torch
ultralytics==8.0.238
```
Install all the dependencies required for this quickstart.
```
pip install -r requirements.txt
```
## Download the model
Run the script and you should have a `best.pt` file in your current directory.
```
python download_model.py
```
## Create a BentoML Service
Create a `service.py` file as follows.
Run `bentoml serve` to start the Service
```
bentoml serve service:svc
```
The serve is now active at http://0.0.0.0:3000. You can interact with it in different ways.
```python
import requests

file_path = "/path/to/your/image.jpg"

with open(file_path, 'rb') as file:
      data = file.read()

headers = {
      "accept": "application/json",
      "Content-Type": "image/png",
}

response = requests.post(
      "http://0.0.0.0:3000/invocation",
      headers=headers,
      data=data,
)

print(response.text)
```
## Build a Bento
After the Service is ready, you can package it into a Bento by specifying a configuration YAML file (`bentofile.yaml`) that defines the build options.
Run `bentoml build` in your project directory to build the Bento
```
bentoml build
```
Run `bentoml models list` to view all available models in the Model Store
View all available Bentos:
```
bentoml list
```
## Serve a Bento
```
bentoml serve yolo_v5_demo:hen2gzrrbckwgnry
```
## Deploy a Bento
To container the Bento with Docker, run:
```
bentoml containerize yolo_v5_demo:hen2gzrrbckwgnry
```
The Docker image's tag is the same as the Bento tag by default. View the created Docker image:
```
docker images
```
Run the Docker image locally:
```
docker run --rm -p 3000:3000 yolo_v8_demo:zqy55uno2w7eerek
docker system df
docker builder prune -af
```
