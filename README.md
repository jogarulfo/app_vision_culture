# AR Monument Recognition — Python Prototype

This prototype demonstrates a simple AR-style monument recognizer in Python.

Features
- Capture frames from webcam or video file
- Recognize monuments via CLIP embeddings -> compare frame and POIs near GPS coordinates of the video source
- Fetch short descriptions from a local JSON or Wikipedia
- Overlay text on frames with OpenCV

# how to run this prototype

1. Add your video to `data/` 

2. Run the app python app.py with replaing your video path and the coordinate of your video source:

Controls
- Press `q` to quit the window.

Notes
- The code attempts to use a CLIP-like model from `sentence-transformers` (`clip-ViT-B-32`) for image embeddings.
- POI data is fetched from a mock function simulating nearby monuments based on GPS coordinates.
- For mobile integration later, this app can be adapted to stream frames and JSON overlays to a mobile frontend.


# Things to improve

- Add real GPS extravtion from video metadata
- Add directional filtering based on compass data
- give as much context as possible to the CLIP model (e.g., nearby POIs, user history, etc)
- use Mapillary or similar datasets for better monument recognition -> compare current image flow with street view images
- get real images of the buildings/monuments from Wikimedia Commons or similar of our poi around -> build a local dataset on the users device
- add a tracker with oencv or yolov to find and then track the monument in the video stream, once lost, we come back to the matching engine
