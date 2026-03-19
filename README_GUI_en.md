# ISED Converter GUI User Guide

## Overview

ISED Converter GUI is a graphical interface tool for converting CB2016 stellar population synthesis model .ised format files.

## Features

- File selection and batch processing
- Support conversion to HDF5, Parquet, and NumPy formats
- Multilingual support (Chinese/English/French)
- Spectral data visualization
- Real-time progress display
- Detailed operation logs
- Comprehensive error handling

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Program

```bash
python ised_gui.py
```

## Usage Instructions

### Conversion Function

1. **Select Input Files**
   - Click the "Select File" button to choose one or more .ised files
   - Or click the "Select Folder" button to choose a folder containing multiple .ised files

2. **Select Output Directory**
   - Click the "Select Output Directory" button to specify where to save the output files

3. **Choose Output Formats**
   - Check the desired output formats (HDF5, Parquet, NumPy)

4. **Start Conversion**
   - Click the "Convert" button to begin conversion
   - The progress bar shows conversion progress
   - The log area displays detailed operation information

### Visualization Function

1. **Load File**
   - Switch to the "Visualization" tab
   - Click the "Load File" button to select a .ised file

2. **View Spectra**
   - Use the time step selector to view spectra at different evolutionary stages
   - Use the toolbar for zooming, panning, and other operations

### Language Switching

- Select "Language" in the menu bar, then choose your preferred language (中文/English/Français)

## File Structure

```
d:\260318_Michaela\
├── ised_gui.py              # Main program file
├── requirements.txt         # Dependency library list
├── README_GUI.md            # Chinese user guide
├── README_GUI_en.md         # English user guide (this file)
├── Michaela_files/
│   └── cb2016_models/
│       ├── ised_converter.py   # Core conversion module
│       └── isedfiles_stars/    # Sample data files
└── back/                   # Backup files
```

## Log Files

Program logs are saved at: `~/.ised_converter/log_YYYYMMDD.log`

## Troubleshooting

### Issue: Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Matplotlib not available

**Solution:**
```bash
pip install matplotlib
```

### Issue: Conversion failed

**Solutions:**
- Verify the input file is a valid .ised format
- Check that you have write permissions for the output directory
- Review the detailed error messages in the log window

## Technical Support

If you encounter problems, please check the log file for detailed error information.

## License

This tool is for academic research purposes only.
