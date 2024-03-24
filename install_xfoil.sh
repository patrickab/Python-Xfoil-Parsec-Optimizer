#!/bin/bash


apt install curl

# Install Homebrew, then add to $PATH
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

apt-get install gfortran
apt-get install build-essential
brew install gcc
apt install libx11-dev

# Clone Xfoil installation repository
git clone https://github.com/christophe-david/XFOIL_compilation.git
cd XFOIL_compilation

# Compile XFOIL, then copy to /bin
./compile.sh
cd bin
cp * /bin/
