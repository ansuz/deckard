## rpi.sh
!/bin/sh

exec bash
sudo apt-get update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev 
sudo apt-get install -y libdb5.3-dev libgdbm-dev libssl-dev libbz2-dev 
sudo apt-get install -y libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
sudo apt-get install -y libsqlite3-dev libc6-dev libbz2-dev python3-setuptools
sudo apt-get install -y build-essential checkinstall openssl wget
wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tar.xz
tar xf Python-3.7.0.tar.xz
cd Python-3.9.0
./configure --enable-optimizations --prefix=/usr
make
sudo make altinstall
cd ..
sudo rm -r Python-3.7.0
rm Python-3.7.0.tar.xz
echo "alias python=/usr/bin/python3.7" > ~/.bashrc
source ~/.bashrc

python -V
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools
python -m pip install --upgrade wheel
python -m pip install --upgrade virtualenv
python -m pip install --upgrade pyyaml
echo "export PATH=\"/home/pi/miniconda3/bin:$PATH\"" > ~/.bashrc
wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-armv7l.sh
sudo /bin/bash Miniconda3-latest-Linux-armv7l.sh
sudo apt-get install libopenblas-dev
sudo apt-get install python-numpy python-scipy python-pandas python-h5py 
sudo apt-get install python3-sklearn python3-sklearn-lib python3-sklearn-doc 

## The above works with really old versions of sklearn, but the below works with the latest version???
# sudo apt instal llvm-9
# LLVM_CONFIG=llvm-config-9 pip install llvmlite

# install berryconda
conda install -c numba llvmdev
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-11.1.0/llvm-11.1.0.src.tar.xz
wget https://github.com/numba/llvmlite

# install llvm from source ?>?>?>?>