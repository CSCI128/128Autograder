export RUNNING_IN_AUTOGRADER=true

echo 'export RUNNING_IN_AUTOGRADER=true' > ~/.bashrc

apt-get install python3 -y
apt-get install python3-pip -y

pip3 install -r /autograder/source/requirements.txt
