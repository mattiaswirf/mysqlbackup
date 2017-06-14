#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Imports
import os
import datetime
from shlex import split as xsplit
import subprocess
from subprocess import check_output, check_call, CalledProcessError
import json
import zipfile
import logging

class MySQLDailyBackup(object):
    """
    Exports all databases (if not in exclude list) as seperate
    backups into date folders. Settings are read from a json file,
    and mysql account used is in a cnf file.
    """

    def __init__(self):
        """
        Initiate this class, set some values,
        and get it's settings from file.
        """
        self.settings = self.get_settings()
        logging.basicConfig(filename=self.settings['log']['file'], level=logging.DEBUG)
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.backup_folder = os.path.join(self.settings['backup_path'], self.today)


    def get_settings(self):
        """
        Get settings from Json file if there
        is one present.
        """
        settings_file_path = os.path.join(os.getcwd(), 'settings.json')
        settings_file = open(settings_file_path)
        return json.load(settings_file)


    def ensure_folder_exists(self, folder):
        """
        Create folder and parent structure,
        if it doesnt exist.
        :param folder: String with the folder (full) path
        :return bool:
        """
        if os.path.isdir(folder):
            return True
        else:
            cmd = "mkdir -p {}".format(folder)
            try:
                check_call(xsplit(cmd))
                return True
            except CalledProcessError as error:
                logging.critical("Backup folder not present: %s", error)
                return False


    def get_db_list(self):
        """
        Get a list of databases.
        :return: List of databasenames or empty list
        """
        cmd = '{} --defaults-extra-file={} -e "SHOW DATABASES"'.format(
            self.settings['mysql']['bin'],
            self.settings['mysql']['account_file']
        )
        databases = []
        try:
            # Run command, get a list split on new line
            output = check_output(xsplit(cmd)).decode('ascii').split("\n")
            # Loop through result and create a list without exluded databases
            for item in output:
                if item not in self.settings['exclude']:
                    databases.append(item)
        except (ValueError, CalledProcessError) as error:
            logging.critical("Could not get a list of databases: %s", error)
        return databases


    def dump_databases(self, databases, folder):
        """
        Loop through a list of databases and dump them.
        :param databases: List with databases
        :param folder: String with the path to save them in
        :return: List with dumped databases or empty list
        """
        successfully_dumped = []
        for dbname in databases:
            if self.dump_database(dbname, folder):
                successfully_dumped.append(dbname)
            else:
                logging.error("Could not dump database: %s", dbname)
        return successfully_dumped


    def dump_database(self, dbname, folder):
        """
        Dump single database to backup file.
        :param dbname: String with databasename
        :param folder: String with folder to save in
        :return: bool
        """
        # Put together the name of resulting SQL file
        sql_file = os.path.join(folder, dbname + '.sql')
        # Create command string for mysqldump
        cmd_string = "{} --defaults-extra-file={} --force --opt --databases {} > {}"
        cmd = cmd_string.format(
            self.settings['mysqldump']['bin'],
            self.settings['mysql']['account_file'],
            dbname,
            sql_file
        )
        # Rund command in pipe
        process = subprocess.Popen(cmd, shell=True)
        # Wait for completion
        process.communicate()
        # Check for errors
        if process.returncode != 0:
            return False
        return True


    def delete_backup(self):
        """
        Delete the daily backup folder.
        :return: bool
        """
        cmd = "rm -rf {}".format(self.backup_folder)
        try:
            check_output(xsplit(cmd))
            return True
        except CalledProcessError as error:
            logging.warning("Could not delete backup folder: %s", error)
            return False


    def run(self):
        """
        Run the backup, dumping db to files.
        :return: list
        """
        if self.ensure_folder_exists(self.backup_folder):
            databases = self.get_db_list()
        if databases:
            dumped = self.dump_databases(databases, self.backup_folder)
        return dumped


def zip_folder(folder, files):
    """
    Create a zip file of todays backup folder.
    :param dumped: list of dumped databases
    """
    try:
        zip_file = zipfile.ZipFile("{}.zip".format(folder), "w")
        for src_file in files:
            zip_file.write("{}/{}.sql".format(folder, src_file), "{}.sql".format(src_file))
        zip_file.close()
        return True
    except RuntimeError:
        return False


def main():
    """
    Create instance of MySQLBackup object
    and run it.
    """
    mysql_backup = MySQLDailyBackup()
    databases = mysql_backup.run()
    if zip_folder(mysql_backup.backup_folder, databases):
        mysql_backup.delete_backup()


if __name__ == "__main__":
    main()
