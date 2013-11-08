#!/usr/bin/python

# This utility compares the release dates of RHEL and CentOS Errata.
# 
# Written by Jason Callaway
# To get the latest version, go to http://github.com/jason-callaway/compare-release-dates

import xmlrpclib
import urllib
import re
import StringIO
from datetime import datetime
from lxml import etree, html
from BeautifulSoup import BeautifulSoup

RHN_ERRATA = 'https://rhn.redhat.com/errata/'
CENTOS_ANNOUNCE = 'http://lists.centos.org/pipermail/centos-announce/'

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']

# TODO: Paramaterize this later
YEAR = '2013'

def get_pretty_html(url):
    html_handler = urllib.urlopen(url)
    html_content = html_handler.read()
    html_parser = html.HTMLParser()
    html_tree = html.parse(StringIO.StringIO(html_content), html_parser)
    return html.tostring(html_tree, pretty_print=True) 

# Walk through the CentOS announce list and get the announcements
centos_announcement_link_list = []
for month in MONTHS:
    # Get the monthly list
    centos_announce_html = get_pretty_html(CENTOS_ANNOUNCE + YEAR + '-' + month)
    
    # We have to convert the html string into a list of lines
    for line in  StringIO.StringIO(centos_announce_html):
        # Look for the line that lists the announcement
        centos_announcements = re.findall(r'.*\[CentOS-announce\].*', line)
        for announcement in centos_announcements:
            # Isolate the CESA, CEEA, and CEBA announcements
            regex = re.compile(r'CE[S|E|A]A')
            if regex.search(announcement):
                soup = BeautifulSoup(announcement)
                # Now isolate the links
                centos_announcement_links = soup.findAll('a')
                for link in centos_announcement_links:
                    # And build the year-month/link string
                    centos_announcement_link_list.append(YEAR + '-' + month + '/' + link['href'])

release_dates = {}
counter = 0
for link in centos_announcement_link_list:
    counter = counter + 1
    centos_name = ''
    centos_date = ''
    rhel_date = ''
    centos_announcement = get_pretty_html(CENTOS_ANNOUNCE + link)
    for line in StringIO.StringIO(centos_announcement):
        regex = re.compile(r'<title> \[CentOS-announce\] CE[S|E|A]A-\d{4}:\d{4}')
        if regex.search(line):
            centos_erratum_name = re.sub(r'.*(CE[S|E|A]A-\d{4}:\d{4}).*', r'\1', line).rstrip('\n')
            centos_name = centos_erratum_name
        match = re.search(r'\w{3}\ \w{3}\ +\d{1,2}\ \d{1,2}:\d{1,2}:\d{1,2}\ UTC\ \d{4}', line)
        if match:
            date_time = re.sub(r'.*(\w{3}\ \w{3}\ +\d{1,2}\ \d{1,2}:\d{1,2}:\d{1,2}\ UTC\ \d{4}).*', r'\1', line).rstrip('\n')
            centos_date = date_time
        match = re.search(r'rhn.redhat.com', line)
        if match:
            soup = BeautifulSoup(line)
            links = soup.findAll('a')
            rhel_announcement = get_pretty_html(links[0]['href'])
            soup = BeautifulSoup(rhel_announcement)
            table = soup.find('table', 'details')
            rows = table.findAll('tr')[3]
            date = rows.findAll('td')[0].string
            rhel_date = date
    release_dates[centos_name] = [centos_date, rhel_date]
#     print '\n' + centos_name + ':'
#     print release_dates[centos_name]
#     if counter > 10:
#         break
    
# print 'centos_announcement [centos_date, rhel_date]'
for key in release_dates:
    centos_date = release_dates[key][0]
    rhel_date = release_dates[key][1]
    c = datetime.strptime(centos_date, '%a %b %d %H:%M:%S UTC %Y')
    r = datetime.strptime(rhel_date, '%Y-%m-%d')
    delta = c - r
    print key + ' delta: ' + str(delta)
    
    