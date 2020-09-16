## Installation instructions
```bash
# Adapted from https://www.brachiograph.art/get-started/install.html
sudo apt-get update
sudo apt-get install python3 python3-pip pigpiod libwebp6 libtiff5 libjbig0 liblcms2-2 libwebpmux3 libopenjp2-7 libzstd1 libwebpdemux2 libjpeg-dev libatlas3-base libgfortran5 git

python3 -m venv env
source env/bin/activate

pip install pigpio pillow numpy tqdm readchar

git clone https://github.com/evildmp/BrachioGraph.git
```