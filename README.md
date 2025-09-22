# PhotoPolarAlign
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

A python utility to help align any equatorial telescope by imaging the Celestial Pole region.

Inspired by Dave Rowe https://web.archive.org/web/20210126061304/http://www.considine.net/aplanatic/align.htm

## 📖 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [What it Doesn't Do](#what-it-doesnt-do)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Building](#building)

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
In the **Releases** tab on the right, go to the latest version and download the program for your computer type.

Or [run the source](#building)

<details>
<summary>For NixOS</summary>

1. Clone this **repository**
```sh
git clone https://github.com/ThemosTsikas/PhotoPolarAlign.git &&
cd PhotoPolarAlign
```
2. Enter development shell
```sh
nix develop ./nix
```
3. **Run**
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
<summary>Local Plate Solving</summary>

Plate solving in local mode runs much faster than Nova (online) and does not require any internet connection.

<details>
<summary>Linux/MacOS</summary>
Astrometry.net provides a downloadable software for doing plate solving on Linux and MacOS systems, as well as potentially Windows Subsystem for Linux (WSL).

1) Download astrometry.net: `apt install astrometry.net` (MacOS use `brew`)
The installation will create the config file `astrometry.cfg` in the `/etc` directory

2) Download the index files for the size of images you will be taking from https://data.astrometry.net/ 
These files contain landmarks of celestial objects to determine where your photo is in the sky. The index files are specific to the FOV your images cover in the sky. Smaller FOVs will need more landmarks and thus larger file sizes. Use this website to determine what files you will want:  https://astrometrynet.readthedocs.io/en/latest/readme.html

3) Move the index files to the directory: `/usr/share/astrometry`

4) Launch PPA.py

5) Open Photo Polar Align ‘Setting’ window

6) Put the following settings in ‘Local Solver Configuration’:
```
shell:   /bin / bash --login -c “%%s”

scale:  commonly 1 or 2  (do some test)

configfile:   /etc/astrometry.cfg 

scale_units:   arcsec/pix 

scale_low and scale_hi:  These define the lower and upper limits of the arcsec/pix value and allow you to reduce any platesolver measurement errors (you can get arcsec/pix value for your specific photographic setup reading it in Nova solving output)

'extra': you can put in some parameters-usually unnecessary and rarely useful-can be given to speed up the platesolving process.
```
7) Click 'Ok': the PPA.ini file will be saved in the PhotoPolarAlign directory.
</details>
<details>
<summary>Windows</summary>

1) Install the ASPS software from: https://www.astrogb.com/astrogb/All_Sky_Plate_Solver.html
It will create  its ~/astrometry/data directory where, through a specific function, it will allow to select the necessary index files and downloading these from the Internet.

2) the configfile is 'backend.cfg'

3) Launch PPA.py

4) Open Photo Polar Align ‘Setting’ window

5) Put the following data in ‘Local Solver Configuration’:
```
   shell:  C:/Users/<user>/AppData/Local/Astrometry/bin/bash --login -c "%%s"

   scale:  commonly 1 or 2  (do some test)

   configfile:  /etc/astrometry/backend.cfg … follow as in Linux

   scale_units:  arcsec/pix 

   scale_low and scale_hi: These define the lower and upper limits of the arcsec/pix value and allow you to reduce any platesolver measurement errors (you can get arcsec/pix value for your specific photographic setup reading it in Nova solving output)

   extra:  put the parameter "-p" to avoid the warning: `FITSFixedWarning: The WCS transformation has more axes (2) than the image it is associated with (0) [astropy.wcs.wcs]`
           related to output: "solve-field.c:327:plot_source_overlay Plotting command failed"
           Windows doesn't have "plotxy" function (it is Linux environment only), but the function is not necessary for us.
```
7) Click 'Ok': the PPA.ini file will be saved in the PhotoPolarAlign directory.
 
</details>
</details>

## Usage
- First, roughly align your telescope with the Celestial Pole region visible in your cameras view from 2 angles, roughly 90 degrees apart.
- Take 2 images: 1 horizontally, and 1 roughly 90 degrees clockwise. Get them onto your computer with PPA installed.
- Run PPA with Python:

On Windows:
```sh
.venv/Scripts/Activate.ps1
python PPA.py
```
On Linux:
```sh
source .venv/bin/activate
python PPA.py
```
On NixOS:
```sh
nix develop ./nix
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


## Building
For testing changes to the program or building the source to run on hardware that don't have installation binaries, you can easily download and run the source code.

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

Or, on NixOS:
1. Clone this **repository**
```sh
git clone https://github.com/ThemosTsikas/PhotoPolarAlign.git &&
cd PhotoPolarAlign
```
2. Enter development shell
```sh
nix develop ./nix
```
3. **Run**
```sh
python PPA.py
```

To build the application:
1. `pip install pyinstaller`
2. `pyinstaller --onefile --add-data "assets:assets" PPA.py`
3. Result will be in `./dist/` folder
