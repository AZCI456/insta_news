# You are correct! Giving the script executable permissions (with `chmod +x pm_setter.sh`) makes it runnable directly (e.g., `./pm_setter.sh on`).
# However, it will still prompt for a password if the `sudo` command requires one.
# To allow running the script without a password, you would need to specifically add a rule to your sudoers file for the `pmset` command (be cautious!):

# For example, run:
#   sudo visudo
# and add a line like:
#   your_username ALL=(ALL) NOPASSWD: /usr/bin/pmset
# This allows your user to run `pmset` without a password.
# Afterward, you can make this script executable: `chmod +x pm_setter.sh`
# Then run it as: `./pm_setter.sh on` or `./pm_setter.sh off`

if [[ "$#" -gt 0 && "$1" == "on" ]]; then
    sudo pmset repeat wake MTWRFSU 08:00:00
    echo "pmset is now on for everyday at 8"
elif [[ "$#" -gt 0 && "$1" == "off" ]]; then
    sudo pmset repeat cancel
    echo "pmset is off"
else
    echo "Enter Valid Argument [\"on\"/\"off\"]"
fi
