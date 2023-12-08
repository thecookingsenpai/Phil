#!/bin/zsh

cd src
pip install -r requirements.txt

cd .. &&
echo "#!/bin/zsh" > run.sh
echo "cd src && python3 phil.py && cd .." >> run.sh
echo "Execute source run.sh to start Phil"