# AI Posture Guardian

**Keep your spine safe while coding and accounting.** An AI-powered computer vision tool that monitors your posture in real-time, alerting you when you slouch or lean too far forward.

---

## Project Overview

As a professional accountant and developer, I spend countless hours at my desk. This project was born from a personal need: **preventing back pain and "tech-neck"** through automation. 

Using **MediaPipe's Pose Estimation**, this script monitors key body landmarks to detect when your posture deviates from a healthy baseline.

## Key Features

* **Custom Calibration:** Set your "Perfect Posture" baseline at each start by pressing `c`.
* **Intelligent Slouch Detection:** Monitors head drop, shoulder misalignment, and forward neck protrusion.
* **Presence Awareness:** Automatically detects when you leave your desk ("NO PERSON DETECTED") to avoid false alarms.
* **Audio Feedback:** Instant macOS system alerts (`afplay`) when bad posture is sustained for more than 3 seconds.
* **Pause/Resume:** Toggle monitoring easily with `p` during breaks or calls.

## Tech Stack

* **Language:** Python 3.11+
* **AI Engine:** MediaPipe (Pose Landmarking)
* **Computer Vision:** OpenCV
* **OS Integration:** Subprocess (macOS System Sounds)

## Keyboard Controls

| Key | Action |
|:---:|:---|
| `c` | **Calibrate** - Set current posture as baseline |
| `p` | **Pause/Resume** - Toggle the monitoring |
| `r` | **Reset** - Clear calibration |
| `q` | **Quit** - Exit the application |

## How it works (Technical Details)

The script calculates several metrics by comparing current landmarks against the calibrated baseline:
1.  **Head Drop:** Normalized distance between the nose and mid-shoulder line.
2.  **Shoulder/Head Angle:** Uses `math.atan2` to detect tilting.
3.  **Z-Depth Protrusion:** Compares the Z-axis (depth) of ears vs. shoulders to catch the "forward neck" position.

---
