# PhotoPolarAlign
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

A python utility to help align any equatorial telescope by imaging the Celestial Pole region.

Inspired by Dave Rowe http://www.considine.net/aplanatic/align.htm

## 📖 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [What it Doesn't Do](#what-it-doesnt-do)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

## Overview

PhotoPolarAlign (PPA) is Python utility that can be used to Polar Align any Equatorial Telescope setup. It works by capturing images of the celestial pole region in two orientations, plate solving their positions, and calculating the error. Users can adjust the telescope and retest for fine alignment.

## Features
✔️ **Graphical User Interface (GUI)**

✔️ **Supports Nova API & Local Plate Solving**

✔️ **Provides Alignment Error** 

✔️ **Works with Any Camera Setup**

## What it Doesn't Do
❌**Take Pictures with Your Camera**

❌**Automatically Align your Telescope**

❌**Point you to a Celestial Object**

## Installation
PhotoPolarAlign is a Python application that currently only runs on Python 2.7. The latest tested version is Python 2.7.18.

### Prerequisites
1. **Install Python 2.7.18**: Download and install from an [official source](https://www.python.org/ftp/python/2.7.18/).
2. **Install Required Python Packages**:
   ```sh
   pip install numpy scipy pillow ujson
   ```
<details>
<summary>
    If you get "Microsoft Visual C++ 9.0 is required"
</summary>

Download Microsoft Visual C++ 9.0 from a web archive [explained here](https://stackoverflow.com/a/67642436/10799348/).
</details>

<details>
<summary>If you are unable to install `ujson`</summary>

The software originally depends on `ujson`, but does not require it if it is unable to be installed.
1. Open `PPA.py` in a text editor.
2. In `json2python` function near top of file
  - Rename variable `json` to something like `data`
3. In `json2python` and `python2json` functions near top of file
  - Replace the `ujson` module with `json`
3. Save the file
4. Install remaining packages with
    ```sh
    pip install numpy scipy pillow
    ```
</details>

## Running PhotoPolarAlign
To launch the software, run it with Python 2.7:
```sh
py -2 PPA.py
```

## Setup
On first startup, a settings page will appear. This can be reaccessed at any time by going to `Files > Settings`.
If you have internet access when you are imaging, you can use <https://nova.astrometry.net> to plate solve your images online. If not, you'll have to install a local plate solver on your device.

<details>
<summary>Nova</summary>

- Create an account on <https://nova.astrometry.net>
- In the top navigation bar, go to "API"
- In the middle in green text is your API key. Copy this, and paste it in the PPA settings where it asks for your nova key
</details>

<details>
<summary>Local: No documentation yet</summary>

Currently no documentation for local setup unfortunately.
</details>

## Usage
- First, roughly align your telescope with the Celestial Pole region visible in your cameras view from 2 angles, roughly 90 degrees apart.
- Take 2 images roughly 90 degrees apart from each other and get them onto your computer with PPA installed.
- Run PPA with Python 2.7:
```sh
py -2 PPA.py
```
- The top part of the interface contains three buttons for uploading your images.
- The **two buttons on the left** are used to input the two initial calibration images you just took.
  - "Solved!" in red means the image has yet to be solved.
- Use the **"nova"** or **"local"** button next to each to run the respective plate solving method.
  - You can watch the terminal to view the status of the solve request. You cannot do anything in the UI until this request finishes.
  - Do not go to your submission in <https://nova.astrometry.net> to attempt to view it's status, as that will close the connection with the program. If you want to view the status of your submission, you can go to the API link that PPA puts into the terminal.
  - "Solved!" in green means the image has been solved.
- Once the two calibration images are solved:
  - Click **"Find Celestial Pole"** to compute and display the alignment error in `HH:MM:SS`.
  - An image will display showing where you are pointed as compared to the actual Celestial Pole.
- Manually adjust your telescope to improve your error.
- You can check your new alignment:
  - Take a single new image and load it using the **rightmost button**.
  - Solve it using the same plate solving method.
  - Click **"Show Improvement"** to see the new error.
  - Repeat this step until your error is small enough (usually under 5 minutes error is perfectly good)

## Troubleshooting
- **Python version errors** → Ensure you are using Python 2.7.18.
- **Missing dependencies** → Install [required packages](#Prerequisites)
- **`ujson` installation fails** → Modify `PPA.py` to use `json` instead.
- **Microsoft Visual C++ 9.0 required** → Install [Microsoft Visual C++ 9.0](#Prerequisites)

## Future Improvements
- Testing and documenting the **local plate solving** feature.
- Explore upgrading for **Python 3 compatibility**.
