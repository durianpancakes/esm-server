# Employee Salary Management Server
# Introduction
This repository is part of my submission for GovTech's ESTL TAP Assessment. This repository is not to be
executed alone as it requires the front end application to work. The front end application can be found 
[here](https://github.com/durianpancakes/esm).

# Setting Up
Disclaimer: The instructions provided assumes that the user is running on Windows.

The project is built with the following: 
* Python 3.10.6
* PostgreSQL 14.5

To avoid any potential problems, please install the above version of Python and PostgreSQL.

1. Install Python 3.10.6 [here](https://www.python.org/downloads/release/python-3106/)

2. Install PostgreSQL [here](https://www.postgresql.org/download/).
   * You may use your own credentials while setting up PostgreSQL. Please remember to change the credentials in 
   lines 15-19 of `app.py` to your credentials.
3. Clone the repository into a directory of your choice.
4. Run ``

# Running the Application
1. Ensure that the [front end](https://github.com/durianpancakes/esm) is set up.
2. At the root directory, using a terminal, run the following:
```
python3 -m venv env
source env/bin/activate
###
# If your system does not allow you to run scripts, run the following command:
Set-ExecutionPolicy RemoteSigned 
###
pip3 install -r requirements.txt
python3 app.py
```
