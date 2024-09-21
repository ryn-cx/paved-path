# Installation is only needed for running benchmarks
pdm install

# Dynamically find the python folder to make the root.pth file in
folder_name=$(realpath .venv/lib/python*)/site-packages/root.pth

# Make the root folder of the project part of the path
echo "../../../.." > $folder_name
