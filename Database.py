# tramtracker -- Real-time tracking of trams in Melbourne, Australia
#
# Database.py - database access routines
#
# Copyright (C) 2009-2010, Danielle Madeley <danielle@madeley.id.au>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import gobject

import sqlite3
import os.path

from math import *

from location import distance_between

# Use Maemo function instead
#
# def deg2rad(deg):
#     return pi * deg / 180
#
# def haversine((lat1, lon1), (lat2, lon2)):
#     R = 6371
#     dLat = deg2rad(lat2 - lat1)
#     dLon = deg2rad(lon2 - lon1)
#     a = sin(dLat / 2) ** 2 + \
#         cos(deg2rad(lat1)) * cos(deg2rad(lat2)) * sin(dLon / 2) ** 2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
#     d = R * c
#     return d

class Database(gobject.GObject):
    __gsignals__ = {
        'database-created': (gobject.SIGNAL_RUN_LAST, None, ())
    }
    conn = None

    def __init__(self):
        gobject.GObject.__init__(self)

        if self.conn is None:
            self.conn = sqlite3.connect(os.path.expanduser('~/.cache/tramtracker.db'))

    def setupStopsTable(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE stops (
                        StopNo INT PRIMARY KEY,
                        FlagStopNo TEXT,
                        StopName TEXT,
                        CrossRoad TEXT,
                        TravelRoad TEXT,
                        CityDirection TEXT,
                        Latitude REAL,
                        Longitude REAL,
                        SuburbName TEXT)''')
        self.conn.commit()
        c.close()
        self.emit('database-created')

    def deleteStop(self, stopNo):
        c = self.conn.cursor()
        c.execute('DELETE FROM stops WHERE stopNo = ?', (stopNo,))

    def storeStop(self, stopinfo):
        c = self.conn.cursor()
        try:
            c.execute('INSERT INTO stops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (int(stopinfo['StopNo']),
                 stopinfo['FlagStopNo'],
                 stopinfo['StopName'],
                 stopinfo.get('CrossRoad', None),
                 stopinfo.get('TravelRoad', None),
                 stopinfo['CityDirection'],
                 stopinfo['Latitude'],
                 stopinfo['Longitude'],
                 stopinfo['SuburbName']))
            self.conn.commit()

        except sqlite3.OperationalError, e:
            if e.message.startswith('no such table'):
                self.setupStopsTable()
                c.close()
                # retry
                self.storeStop(stopinfo)
                return
            else:
                raise e

        except sqlite3.IntegrityError, e:
            if e.message.startswith('column StopNo is not unique'):
                c.execute('''UPDATE stops SET
                                FlagStopNo=?,
                                StopName=?,
                                CrossRoad=?,
                                TravelRoad=?,
                                CityDirection=?,
                                Latitude=?,
                                Longitude=?,
                                SuburbName=?
                                WHERE StopNo = ?''',
                    (int(stopinfo['StopNo']),
                     stopinfo['FlagStopNo'],
                     stopinfo['StopName'],
                     stopinfo.get('CrossRoad', None),
                     stopinfo.get('TravelRoad', None),
                     stopinfo['CityDirection'],
                     stopinfo['Latitude'],
                     stopinfo['Longitude'],
                     stopinfo['SuburbName']))
                self.conn.commit()
            else:
                raise e

        c.close()

    def getStop(self, stopNo):
        c = self.conn.cursor()
        try:
            rows = c.execute('SELECT * FROM stops WHERE StopNo = ?', (stopNo,))
        except sqlite3.OperationalError, e:
            if e.message.startswith('no such table'):
                self.setupStopsTable()
                c.close()
                return {}
            else:
                raise e

        try:
            row = dict(zip(map(lambda a: a[0], rows.description), rows.fetchone()))
        except TypeError, e:
            raise Exception("Unknown Stop ID %s" % stopNo)

        c.close()
        return row

    def getStreets(self, street=None):
        query = 'SELECT StopName, CrossRoad, TravelRoad FROM stops'

        if street:
            query += ' WHERE StopName = ? OR CrossRoad = ? OR TravelRoad = ?'
            params = (street, street, street)
        else:
            params = ()

        c = self.conn.cursor()
        try:
            rows = c.execute(query, params)
        except sqlite3.OperationalError, e:
            if e.message.startswith('no such table'):
                self.setupStopsTable()
                c.close()
                return []
            else:
                raise e

        roads = set()

        for stopName, crossRoad, travelRoad in rows:
            addStopName = True

            if crossRoad and travelRoad:
                roads.add(crossRoad)
                roads.add(travelRoad)
            else:
                roads.add(stopName)

        if street: roads.remove(street)

        roads = list(roads)
        roads.sort()

        return roads

    def getStops(self, stopName=None, street1=None, street2=None):
        query = 'SELECT StopNo, FlagStopNo, StopName, CityDirection, SuburbName FROM stops '

        if stopName:
            query += ' WHERE StopName = ?'
            params = (stopName,)
        elif street1 and street2:
            query += ''' WHERE (CrossRoad = ? AND TravelRoad = ?) OR
                               (TravelRoad = ? AND CrossRoad = ?)'''
            params = (street1, street2, street1, street2)

        c = self.conn.cursor()
        try:
            rows = c.execute(query, params)
        except sqlite3.OperationalError, e:
            if e.message.startswith('no such table'):
                self.setupStopsTable()
                c.close()
                return []
            else:
                raise e

        stops = map(lambda row: dict(zip(map(lambda a: a[0], rows.description), row)), rows)
        c.close()

        return stops

    def getNearbyStops(self, lat, long, exclude_stop=0):
        c = self.conn.cursor()

        RANGE = 0.005

        rows = c.execute('''SELECT StopNo, FlagStopNo, StopName, CityDirection, SuburbName, Latitude, Longitude FROM stops WHERE StopNo != ? AND StopNo IN
            (SELECT StopNo FROM stops WHERE Latitude BETWEEN ? and ?
             INTERSECT
             SELECT StopNo FROM stops WHERE Longitude BETWEEN ? and ?)''',
             (exclude_stop, lat - RANGE, lat + RANGE, long - RANGE, long + RANGE))

        stops = map(lambda row: dict(zip(map(lambda a: a[0], rows.description), row)), rows)
        c.close()

        for stop in stops:
            stop['Distance'] = distance_between(lat, long,
                                stop['Latitude'], stop['Longitude'])

        stops.sort(cmp = lambda a, b: cmp(a['Distance'], b['Distance']))

        return stops

gobject.type_register(Database)
