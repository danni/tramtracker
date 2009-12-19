import sqlite3

class Database(object):
    conn = None

    def __init__(self):
        if self.conn is None: self.conn = sqlite3.connect('tramtracker.db')

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
        rows = c.execute('SELECT * FROM stops WHERE StopNo = ?', (stopNo,))
        if len(rows) > 1:
            raise Exception("Too many rows returned for stopNo %i" % stopNo)

        c.close()
        return rows.fetchone()

    def getStreets(self, street=None):
        query = 'SELECT StopName, CrossRoad, TravelRoad FROM stops'

        if street:
            query += ' WHERE StopName = ? OR CrossRoad = ? OR TravelRoad = ?'
            params = (street, street, street)
        else:
            params = ()

        c = self.conn.cursor()
        rows = c.execute(query, params)
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
        rows = list(c.execute(query, params))
        c.close()

        return rows
