#!/usr/bin/env python

"""
USAGE:
./log_parser.py FILE
This script takes the full or relative path to ONE log file as an argument
and then generates a Sensu readable output. The output represent the health
check status of FILE.

Ref for Sensu output:
https://sensuapp.org/docs/latest/reference/checks.html#sensu-check-specification

> Result data is output to STDOUT or STDERR
    > For standard checks this output is typically a human-readable message
    > For metrics checks this output contains the measurements
      gathered by the check
> Exit status code indicates state
    > 0 indicates "OK"
    > 1 indicates "WARNING"
    > 2 indicates "CRITICAL"
    > exit status codes other than 0, 1, or 2
      indicate an "UNKNOWN" or custom status
"""

import os
import time
import sys
from dateutil.parser import parse

# Define variables:
current_epoc_time = time.time()
current_year = time.strftime("%Y")


def date_convert_to_epoch(date):
    """ convert date to Epoch time.
    Convert a given date to Unix time (also known as Epoch time)
    Args:
        date: String represent date in '%Y %b %d %H:%M:%S' format.
    Returns:
        An integer value of the Epoch time.
    Raises:
        ValueError: Unknown string format
    """
    try:
        parse(date)
        strip_time = time.strptime(date, '%Y %b %d %H:%M:%S')
        return int(time.mktime(strip_time))
    except ValueError as e:
        print e
        sys.exit(1)


def convert_logs(raw_file):
    """ Take a file as in put a convert unify all time entries
    Args:
        raw_file: String represent a file path.
    Returns:
        Nested list of time and message of each line.
    Raises:
        None
    """
    with open(raw_file, 'r') as file:
        lines = []
        for line in file:
            if (line.split()[0]).isdigit():
                lines.append(line.split(None, 1))
            else:
                # To fix irregularity in whitespace numbers
                # after the month string
                whitespaces = (line[:5]).count(" ")
                # Convert %b %d %H:%M:%S to Epoch time
                d_month, d_day, d_time = line.split()[:3]
                # We need current year to improve Epoch time accuracy
                d_string = "{} {} {} {}".format(
                    current_year,
                    d_month,
                    d_day,
                    d_time)
                # Pay close attention to white spaces in d_logged
                d_logged = "{}{}{} {}".format(
                    d_month,
                    " " * whitespaces,
                    d_day,
                    d_time)
                log_epoch = date_convert_to_epoch(d_string)
                line_epoch = line.replace(d_logged, str(log_epoch))
                line_split = line_epoch.split(None, 1)
                lines.append(line_split)
        return lines


def parse_logs(logfile):
    """ Parse a file and performs some health checks.

    Args:
        logfile: String represent a file path.
    Returns:
        Print health check result and/or exit using according system exit code.
    Raises:
        None
    """
    last = int(convert_logs(logfile)[-1][0])
    if current_epoc_time - last >= 3600:
        print "WARNING - There has been no log entries during the last hour"
        sys.exit(1)
    else:
        for epoch_time, message in convert_logs(logfile):
            if int(epoch_time) > (current_epoc_time - 600):
                if "WARNING" in message:
                    print "WARNING - Warning message found within last 10 minutes"
                    sys.exit(1)
                elif "ERROR" in message:
                    print "CRITICAL - ERROR message found within last 10 minutes"
                    sys.exit(2)
        sys.exit(0)


if __name__ == "__main__":
    # To make sure only one argument provided to run tis script.
    if not len(sys.argv) > 0:
        print "WARNING - No PATH argument provided"
        sys.exit(1)
    logfile_name = sys.argv[1]
    try:
        input_file = os.path.exists(logfile_name)
    except IOError:
        print "CRITICAL - log file does not exist"
        sys.exit(2)
    parser_report = parse_logs(logfile_name)
    print (parser_report)
