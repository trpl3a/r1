# XML E-Sign Analyzer - User Guide

## Overview
This web application allows you to analyze XML files to identify buttons that don't have the "e sign" feature properly configured. It processes multiple XML files at once and provides results in both text and CSV formats.

## Features
- Upload multiple XML files simultaneously
- Drag-and-drop interface for easy file selection
- Automatic detection of buttons missing e-sign configuration
- Results displayed in an organized, user-friendly format
- Export results as CSV or plain text files
- Responsive design that works on desktop and mobile devices

## How It Works
The application scans each XML file for `<button>` elements and checks if they have an `<eSignature>` element with the `requireElectronicSignature` attribute set to "true". Buttons that are missing this configuration are flagged and included in the results.

## How to Use
1. Access the web application through your browser
2. Upload XML files by either:
   - Dragging and dropping files onto the upload area
   - Clicking the "Browse Files" button and selecting files
3. Wait for the files to be processed
4. Review the results displayed on the page
5. Download the results in your preferred format (CSV or text)

## Technical Details
- Built with Flask (Python web framework)
- Uses XML parsing to identify missing e-sign configurations
- Supports batch processing of multiple files
- Maintains session data for result persistence

## Deployment Instructions
1. Ensure Python 3.6+ is installed on your system
2. Install required dependencies: `pip install -r requirements.txt`
3. Run the application: `python src/main.py`
4. Access the application at http://localhost:5000

## Requirements
- Python 3.6 or higher
- Flask
- Web browser with JavaScript enabled
