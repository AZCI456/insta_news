# do this in another virtual environment - separate from the main instaloader extraction

# create the virtual environment
 if [ ! -d ".venv" ]; then
    python3 -m venv .venv
 fi

# activate the virtual environment
source .venv/bin/activate # to activate the virtual environment.

# install the dependencies
pip3 install beautifulsoup4 requests dotenv tqdm # -r requirements.txt is the better way to do this but i'm lazy
# tqdm from prev project shows the progress bar for the for loop
