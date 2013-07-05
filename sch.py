#!/usr/bin/env python
# # -*- Mode: Python; tab-width: 4 -*-
#
# Schedule Dumper
#
# tool per la generazione del file current.gap
# a partire dall'url http://www.di.unipi.i/~paolo/Orario/docenti.htm
#
# Author: Leonardo
# Gruppo Beatrice <http://beatrice.cli.di.unipi.it>
#
# This software is distribuited AS IS, WITHOUT ANY WARRANTY. Feel free
# to use it and customize it.
#
# ===========================================================================
## @file sch.py
## Schedule Dumper


__doc__ = 'Schedule dumper'
__version__ = '0.9'


from urllib import URLopener
import sys
import re
from HTMLParser import HTMLParser
from getopt import getopt, GetoptError

class TTParser(HTMLParser):
    """
        Personalized HTML Parser to parse a teacher' schedule
        table
    """

    def __init__(self, people):
        self.inTr = False
        self.inTd = False
        self.rownumber = -1
        self.colnumber = -1
        self.schedule = []
        self.people = people
        self.cols = ['day', 'room', 'start', 'stop', 'course']
        self.days = {'Lun':1, 'Mar':2, 'Mer':3, 'Gio':4, 'Ven':5}
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'tr' and not self.inTr:
            self.inTr = True
            self.rownumber = self.rownumber + 1
        elif tag.lower() == 'td' and not self.inTd:
            self.inTd = True
            self.colnumber = self.colnumber + 1

    def handle_endtag(self, tag):
        if tag.lower() == 'tr' and self.inTr:
            self.inTr = False
            if len(self.schedule) > 0:
                self.schedule[self.rownumber - 1]['people'] = self.people
            self.colnumber = -1
        elif tag.lower() == 'td' and self.inTd:
            self.inTd = False

    def handle_data(self, data):
        if self.inTr:
            if self.colnumber >= 0 and self.rownumber > 0:
                if len(self.schedule) <= self.rownumber - 1:
                    self.schedule.append({})
                if self.cols[self.colnumber] == 'day':
                    data = self.days[data]
                self.schedule[self.rownumber - 1][self.cols[self.colnumber]] = data

    def get_list(self):
        return self.schedule


URL_PROTOCOL = 'http'
URL_DOMAIN = 'www.di.unipi.it'
URL_SUBPATH = '~paolo/Orario'

if __name__ == '__main__':
    output = "./current.gap"
    try:
        opts, args = getopt(sys.argv[1:], "o:h")
        for opt, arg in opts:
            if opt == '-h':
                print """
    usage: %s [-o output | -h]

    options:
    -h: print this help screen
    -o output: write into output file
               generated content
                      """ % sys.argv[0]
                sys.exit(1)
            elif opt == '-o':
                output = arg
    except GetoptError:
        print "Wrong parameters. type  %s -h for usage" % sys.argv[0]
        sys.exit(2)

    # Richiesta del file con l'elenco insegnanti
    print "Reading people..."
    names = URLopener().open("%s://%s/%s/docenti.htm" % (URL_PROTOCOL, URL_DOMAIN, URL_SUBPATH))

    # foreach insegnante
    courses = []
    for line in names.readlines():
        key = re.sub("\<\/?[a-zA-Z]+([ a-zA-Z]+\=\"[\S]*\")*\>|\n", "", line)
        value = re.match("(.*)href\=\"(?P<url>[\S]*)\"(.*)", line).group('url')

        # richiedi la pagina insegnante
        print "Retrieve %s..." % value
        course = URLopener().open("%s://%s/%s/%s" % (URL_PROTOCOL, URL_DOMAIN, URL_SUBPATH, value))
        parser = TTParser(key)
        #   parsing orario, corso
        parser.feed(course.read())
        courses.extend(parser.get_list())

    #   inserimento in current.gap
    print "Generation complete. Writing on %s..." % output
    out = file(output, 'w')
    for c in courses:
        if not "(sp)" in c['room']:
            out.write("%s ; %s ; %s ; %s:00 ; %s:00 ; %s ; 0 ; inf ; 2607\n" % (c['day'], c['course'], c['room'], c['start'], c['stop'], c['people']))

    out.write("\n")
    out.close()
    print "All Done!"
