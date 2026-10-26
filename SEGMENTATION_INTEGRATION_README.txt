RDDS optional segmentation integration
=====================================

What changed
------------
- Added app/services/segmentation_service.py for YOLO segmentation inference.
- Added an inspection mode selector: Detection (default) or Segmentation (experimental).
- The selected mode is sent to the existing Flask analysis endpoint.
- Segmentation predictions are rendered to the existing annotated-image output path.
- Existing Detection rows continue storing each instance's class, confidence and bounding box.
- The existing Inspection.model_name column records the model mode; no database schema migration is required.
- Added SEGMENTATION_MODEL_PATH to config.py.
- Added Ultralytics to requirements.txt if it was not already listed.

Before running
--------------
1. Back up your current RDDS project folder.
2. Extract this ZIP and copy/merge its files into your project, preserving the folder paths.
3. Copy your trained checkpoint from Google Drive:
      rdds_yolo11n_seg_best.pt
   into the project's:
      models/rdds_yolo11n_seg_best.pt
4. Ensure config.py is in the project root beside run.py and requirements.txt.
5. Activate your existing virtual environment and install the added dependency if needed:
      pip install -r requirements.txt
6. Start the application using your usual command (for example, python run.py).
7. Test standard Detection mode first, then try Segmentation mode with a sample image.

Optional configuration
----------------------
Set SEGMENTATION_MODEL_PATH in your environment if the checkpoint is stored elsewhere.
The standard detector still uses MODEL_PATH and remains the default mode.

Important
---------
The segmentation model is experimental and was trained on a very small polygon dataset.
It must not be treated as safety-critical or as a replacement for professional inspection.
The displayed segmentation mask is saved as an annotated image. The current database stores
bounding boxes in Detection rows, not the full pixel mask; mask geometry is not stored in SQL.

Security note
-------------
The provided config.py uses a development fallback SECRET_KEY. For deployment, set a strong
SECRET_KEY environment variable. Do not commit secrets or user data to source control.
