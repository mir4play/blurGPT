# BlurGPT Roadmap

This roadmap describes the next technical priorities for BlurGPT. It is intentionally kept separate from the changelog: the roadmap describes future work, while the changelog records work that has already been released.

## Current priorities

### 1. Improve detection/tracking robustness

The current pipeline uses one YOLO model for both faces and license plates and uses lightweight motion prediction between detector calls.

Next improvements should focus on reducing temporal errors caused by:

- objects appearing or disappearing between detector calls
- occlusion
- ambiguous nearest-center matches
- changes in object count
- rapid object movement

Potential approaches include a dedicated object tracker, IoU-based matching, ByteTrack or BoT-SORT.

### 2. Better exception handling and recovery

Strengthen failure handling around:

- unreadable/corrupt video files
- decoder failures
- encoder failures
- missing model files
- invalid configuration
- interrupted processing

The goal is to make batch processing fail gracefully and preserve enough state to diagnose the affected job.

### 3. Batch-processing improvements

Improve the job lifecycle and reporting for larger collections of videos, including clearer job states and more useful failure information.

### 4. Model development

The project is continuing to develop and evaluate improved training data and model versions for combined face and license-plate detection.

Model-training experiments should be documented separately from the runtime architecture so that the README always describes the model actually shipped with the application.

## Under evaluation

- Kalman Filter
- Optical Flow
- Object Tracking
- Additional anonymization methods
- GUI

## Completed since the previous roadmap

The following items previously appeared as future work but are now part of the current implementation:

- Combined face and license-plate detection through a single runtime model
- Motion prediction between YOLO detections
- Modular detector/detection architecture
- Batch job workflow
- Automatic input archiving

These should not be re-added to the planned-work list unless a new implementation is being proposed.
