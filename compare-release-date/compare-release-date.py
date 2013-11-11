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

# We could modify this to use local versions of centos-announce, and talk to a 
# local Satellite via the XML-RPC API, which would make it run much faster, but 
# for now this is good.
RHN_ERRATA = 'https://rhn.redhat.com/errata/'
CENTOS_ANNOUNCE = 'http://lists.centos.org/pipermail/centos-announce/'

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']

#TODO: Parameterize this later.
# For now, just edit the year 
YEAR = '2012'

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
# Now iterate over the list of CentOS announcements
for link in centos_announcement_link_list:
    # Just in case an interation fails (there are some bugs), zero out the 
    # strings we use for matching
    centos_name = ''
    centos_date = ''
    rhel_date = ''
    
    # Get the announcement
    centos_announcement = get_pretty_html(CENTOS_ANNOUNCE + link)
    # The is the slow part.  For each line in the html document, do a bunch
    # of pattern matching
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
            # Ok, now we've found the RHN announcement.  Let's get that and
            # parse it, which is a little easier since it's HTML and not a 
            # list announcement
            soup = BeautifulSoup(line)
            links = soup.findAll('a')
            rhel_announcement = get_pretty_html(links[0]['href'])
            soup = BeautifulSoup(rhel_announcement)
            table = soup.find('table', 'details')
            rows = table.findAll('tr')[3]
            date = rows.findAll('td')[0].string
            rhel_date = date
    
    # If you want to watch progress, leave these lines uncommented.
    release_dates[centos_name] = [centos_date, rhel_date]
    print '\n' + centos_name + ':'
    print release_dates[centos_name]
    
# print 'centos_announcement [centos_date, rhel_date]'
for key in release_dates:
    try:
        centos_date = release_dates[key][0]
        rhel_date = release_dates[key][1]
    except:
        print "---FAILED ON release_dates:" + key
    if rhel_date:
        try:    
            c = datetime.strptime(centos_date, '%a %b %d %H:%M:%S UTC %Y')
            r = datetime.strptime(rhel_date, '%Y-%m-%d')
        except:
            print "---FAILED ON strptime:" + key
        try:    
            delta = c - r
            days = ((delta.total_seconds() / 60) / 60 ) / 24
            print key + ' delta: ' + str(days)
        except Exception, e:
            print "---FAILED ON delta subtraction:" + key
            print e    
    