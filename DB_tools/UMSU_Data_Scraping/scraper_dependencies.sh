# do this in another virtual environment - separate from the main instaloader extraction

# create the virtual environment
python3 -m venv .venv

# activate the virtual environment
source .venv/bin/activate

# install the dependencies
pip3 install beautifulsoup4 requests # -r requirements.txt is the better way to do this but i'm lazy

