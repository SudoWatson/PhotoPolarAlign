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
<details>
<summary>Windows</summary>

1. Make sure you have **Python 3** installed on your device
2. Clone this **repository**
```sh
git clone https://github.com/ThemosTsikas/PhotoPolarAlign.git &&
cd PhotoPolarAlign
```
3. Create a **Virtual Environment**
```sh
python -m venv .venv &&
.venv/Scripts/Activate.ps1
```
4. Install **Required Python Packages**:
```sh
pip install numpy scipy pillow configparser astropy
```
5. **Run**
```sh
python PPA.py
```
</details>

<details>
<summary>Linux</summary>

1. Make sure you have **Python 3** installed on your device
2. Clone this **repository**
```sh
git clone https://github.com/ThemosTsikas/PhotoPolarAlign.git &&
cd PhotoPolarAlign
```
3. Install **TKinter** if it does not come with your Python installation
```sh
apt install python3-tk
```
4. Create a **Virtual Environment**
```sh
python -m venv --system-site-packages .venv &&
source .venv/bin/activate
```
5. Install **Required Python Packages**:
```sh
pip install numpy scipy pillow configparser astropy
```
6. **Run**
```sh
python PPA.py
```
</details>


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
- Take 2 images: 1 horizontally, and 1 roughly 90 degrees clockwise. Get them onto your computer with PPA installed.
- Run PPA with Python:
```sh
python PPA.py
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
  - The error in dd:mm:ss will display for each axis.
- Manually adjust your telescope to improve your error.
- You can check your new alignment:
  - Take a single new image and load it using the **rightmost button**.
  - Solve it using the same plate solving method.
  - Click **"Show Improvement"** to see the new error.
  - Repeat this step until your error is small enough (usually under 5 minutes error is perfectly good)
