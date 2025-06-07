# bt-object-placement-is
Bachelor thesis: Information system for determining the location of objects in transport network nodes

# How to build for Windows
```
pip install -r requirements.txt
pip install -e .
pyinstaller main.py --onefile --windowed --hiddenimport win32timezone --name ObjectPlacementApp --specpath .
```
