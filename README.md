# MySQL Backup

This is just a simple mysql /mariadb daily backup script written in Python, only tested on Ubuntu Linux (as my servers are using Ubuntu). Nothing fancy really, it backs up all databases on selected server and creates a zipfile. I have been planning to also include upload to a cloud service but that's not implemented yet.

## Usage

* Copy the file settings.example.json to settings.json and change settings.
* Point the setting "mysql"."account_file" to a mysql .cnf file with contents similar to the included account.example.cnf,  that contains login credentials for mysql.
* Run the script as root (with sudo).

Feel free to suggest improvements.