import os
import sqlite3

class AirwayLeg:
    def __init__(self, awy_id, level, wp1_id, wp2_id):
        self.awy_id = awy_id
        self.level = level
        self.wp1_id = wp1_id
        self.wp2_id = wp2_id
        self.prev = None
        self.succ = None

def insert_fix(fix_file, cursor, connect):
    # Read data from file A and insert into Waypoints table
    with open(fix_file, 'r') as file:
        cursor.execute('SELECT COUNT(*) FROM Waypoints')
        id_start = cursor.fetchone()[0] + 1
        for line in file:
            # Parse the line to extract relevant information
            parts = line.strip().split()
            latitude = float(parts[0])
            longitude = float(parts[1])
            ident = parts[2]  # Correct index for 'Ident'
            country = parts[4]
            name = ''.join(parts[6:])  # Combine the remaining parts as Name

            cursor.execute('SELECT COUNT(*) FROM WaypointLookup WHERE Ident = ? and Country = ?', (ident, country))
            count = cursor.fetchone()[0]
            if count == 0:
                # Insert the data into the Waypoints table
                cursor.execute('''
                    INSERT INTO Waypoints (Ident, Collocated, Name, Latitude, Longtitude)
                    VALUES (?, ?, ?, ?, ?);
                ''', (ident, False, name, latitude, longitude))
                cursor.execute('''
                    INSERT INTO WaypointLookup (Ident, Country, ID)   
                    VALUES (?, ?, ?);         
                ''', (ident, country, id_start))
                id_start += 1
    connect.commit()

def insert_airways(awy_file, cursor, connect):
    awy_set = set()
    with open(awy_file, 'r') as file:
        for line in file:
            airway = line.strip().split()[-1]
            if '-' in airway:
                awy_set.update(airway.split('-'))
            else:
                awy_set.add(airway)
    for elem in awy_set:
        cursor.execute('SELECT COUNT(*) FROM Airways WHERE Ident = ?', (elem,))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('INSERT INTO Airways (Ident) VALUES (?)', (elem,))
    connect.commit()

def update_leg_map(cursor, legmap, legSrcMap, legDestMap, wp1, wp1_country, wp2, wp2_country, dir, lvl, awy):
    cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country = ?', (wp1, wp1_country))
    fetched = cursor.fetchone()
    if fetched == None:
        print(wp1, wp1_country)
    wp1_id = fetched[0]
    #wp1_id = cursor.fetchone()[0]
    cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country = ?', (wp2, wp2_country))
    wp2_id = cursor.fetchone()[0]
    cursor.execute('SELECT ID FROM Airways WHERE Ident = ?', (awy,)) #the comma can not be ignored
    awy_id = cursor.fetchone()[0]
    if dir == 'F':
        leg = AirwayLeg(awy_id, lvl, wp1_id, wp2_id)
        idx = (leg.awy_id, leg.wp1_id, leg.wp2_id)
        if legmap.get(idx) == None:
            legmap[idx] = leg
            legSrcMap[(leg.awy_id, leg.wp1_id)] = leg
            legDestMap[(leg.awy_id, leg.wp2_id)] = leg
            if legSrcMap.get((leg.awy_id, leg.wp2_id)) != None:
                succ_leg = legSrcMap[(leg.awy_id, leg.wp2_id)]
                succ_leg.prev = leg
                leg.succ = succ_leg
            if legDestMap.get((leg.awy_id, leg.wp1_id)) != None:
                prev_leg = legDestMap[(leg.awy_id, leg.wp1_id)]
                prev_leg.succ = leg
                leg.prev = prev_leg
        else:
            if legmap[idx].level != leg.level:
                legmap[idx].level = 'B'    #in both IFR low and IFR high
    else:
        leg1 = AirwayLeg(awy_id, lvl, wp1_id, wp2_id)
        leg2 = AirwayLeg(awy_id, lvl, wp2_id, wp1_id)
        idx1 = (leg1.awy_id, leg1.wp1_id, leg1.wp2_id)
        idx2 = (leg2.awy_id, leg2.wp1_id, leg2.wp2_id)
        if legmap.get(idx1) == None:
            legmap[idx1] = leg1
            legSrcMap[(leg1.awy_id, leg1.wp1_id)] = leg1
            legDestMap[(leg1.awy_id, leg1.wp2_id)] = leg1
            if legSrcMap.get((leg1.awy_id, leg1.wp2_id)) != None:
                succ_leg = legSrcMap[(leg1.awy_id, leg1.wp2_id)]
                succ_leg.prev = leg1
                leg1.succ = succ_leg
            if legDestMap.get((leg1.awy_id, leg1.wp1_id)) != None:
                prev_leg = legDestMap[(leg1.awy_id, leg1.wp1_id)]
                prev_leg.succ = leg1
                leg1.prev = prev_leg
        else:
            if legmap[idx1].level != leg1.level:
                legmap[idx1].level = 'B'
        if legmap.get(idx2) == None:
            legmap[idx2] = leg2
            legSrcMap[(leg2.awy_id, leg2.wp1_id)] = leg2
            legDestMap[(leg2.awy_id, leg2.wp2_id)] = leg2
            if legSrcMap.get((leg2.awy_id, leg2.wp2_id)) != None:
                succ_leg = legSrcMap[(leg2.awy_id, leg2.wp2_id)]
                succ_leg.prev = leg2
                leg2.succ = succ_leg
            if legDestMap.get((leg2.awy_id, leg2.wp1_id)) != None:
                prev_leg = legDestMap[(leg2.awy_id, leg2.wp1_id)]
                prev_leg.succ = leg2
                leg2.prev = prev_leg
        else:
            if legmap[idx2].level != leg2.level:
                legmap[idx2].level = 'B'

def insert_airwaylegs(awy_file, cursor, connect):
    legmap = {}
    legSrcMap = {}
    legDestMap = {}
    with open(awy_file, 'r') as file:
        for line in file:
            parts = line.strip().split()
            wp1 = parts[0]
            wp1_country = parts[1]
            wp2 = parts[3]
            wp2_country = parts[4]
            dir = parts[6]
            if parts[7] == '1':
                lvl = 'L'
            else:
                lvl = 'H'
            awy_str = parts[10]
            if '-' in awy_str:
                awys = awy_str.strip().split('-')
                for awy in awys:
                    update_leg_map(cursor, legmap, legSrcMap, legDestMap, wp1, wp1_country, wp2, wp2_country, dir, lvl, awy)
            else:
                update_leg_map(cursor, legmap, legSrcMap, legDestMap, wp1, wp1_country, wp2, wp2_country, dir, lvl, awy_str)
        for leg in legmap.values():
            start = False
            end = False
            if leg.prev == None:
                start = True
            if leg.succ == None:
                end = True
            cursor.execute('''
                INSERT INTO AirwayLegs (AirwayID, Level, Waypoint1ID, Waypoint2ID, IsStart, IsEnd)
                VALUES (?, ?, ?, ?, ?, ?)         
            ''', (leg.awy_id, leg.level, leg.wp1_id, leg.wp2_id, start, end))
        connect.commit()

def insert_airports_and_runways(src_db, data_path, cursor, connect):
    src_conn = sqlite3.connect(src_db)
    src_cur = src_conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM Airports')
    apt_id_start = cursor.fetchone()[0] + 1
    for root, dirs, files in os.walk(data_path):
        for file in files:
            icao_string = file[:-4]
            src_cur.execute('''SELECT Name, ICAO, Latitude, Longtitude, Elevation, 
                        TransitionAltitude, TransitionLevel, SpeedLimit, SpeedLimitAltitude, ID
                        FROM Airports WHERE ICAO = ?
                        ''', (icao_string,))
            src_rec = src_cur.fetchone()
            if src_rec == None:
                with open(data_path + file, 'r') as file_content:
                    apt_inserted = False
                    for line in file_content:
                        data_vec = line.strip().split(',')
                        if data_vec[0][0:4] == 'RWY:':
                            rwy_ident = data_vec[0].strip().split(':')[1][2:]
                            if rwy_ident[-1] == ' ':
                                rwy_ident = rwy_ident[:-1]
                            lat_str = data_vec[7].strip().split(';')[1]
                            lon_str = data_vec[8]
                            
                            if lat_str[0] == 'N':
                                lat_sign = 1
                            else:
                                lat_sign = -1

                            if lon_str[0] == 'E':
                                lon_sign = 1
                            else:
                                lon_sign = -1

                            lat_float = lat_sign * (float(lat_str[1:3]) + (float(lat_str[3:5]) / 60) + (float(lat_str[5:]) / 100 / 3600))
                            lon_float = lon_sign * (float(lon_str[1:4]) + (float(lon_str[4:6]) / 60) + (float(lon_str[6:]) / 100 / 3600))
                            #print(rwy_ident + ' ' + str(lat_float) + ' ' + str(lon_float))
                            if apt_inserted == False:
                                cursor.execute('''
                                    INSERT INTO Airports (Name, ICAO, Latitude, Longtitude, Elevation, 
                                        TransitionAltitude, TransitionLevel, SpeedLimit, SpeedLimitAltitude)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', ('UNKNOW', icao_string, lat_float, lon_float, 1000, 9850, 11800, 250, 10000))
                                apt_inserted = True
                            true_heading = float(rwy_ident[:2]) * 10 - 7
                            cursor.execute('''
                                INSERT INTO Runways (AirportID, Ident, TrueHeading, Length, Width, Surface, Latitude, Longtitude, Elevation)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)            
                            ''', (apt_id_start, rwy_ident, true_heading, 11800, 148, 'CON', lat_float, lon_float, 1000))
                    apt_id_start += 1
            else:
                cursor.execute('SELECT ID FROM Airports WHERE ICAO = ?', (icao_string,))
                if cursor.fetchone() == None:
                    cursor.execute('''
                        INSERT INTO Airports (Name, ICAO, Latitude, Longtitude, Elevation, 
                                TransitionAltitude, TransitionLevel, SpeedLimit, SpeedLimitAltitude)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (src_rec[0], src_rec[1], src_rec[2], src_rec[3], src_rec[4],
                        src_rec[5], src_rec[6], src_rec[7], src_rec[8]))
                    src_cur.execute('''
                        SELECT Ident, TrueHeading, Length, Width, Surface, Latitude, Longtitude, Elevation
                        FROM Runways WHERE AirportID = ?
                    ''', (src_rec[-1],))
                    for src_rwy_rec in src_cur.fetchall():
                        cursor.execute('''
                            INSERT INTO Runways (AirportID, Ident, TrueHeading, Length, Width, Surface, Latitude, Longtitude, Elevation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (apt_id_start, src_rwy_rec[0], src_rwy_rec[1], src_rwy_rec[2], src_rwy_rec[3], src_rwy_rec[4], src_rwy_rec[5], src_rwy_rec[6], src_rwy_rec[7]))
                    apt_id_start += 1
        connect.commit()
    src_conn.close()


path_start = 'E:\\导航数据\\'
CIFP_PATH = path_start + 'CIFP\\'
FIX_DATASET = {'FIX.dat', 'FIX_ZPJH.dat', 'FIX_ZPLJ.dat', 'FIX_ZPMS.dat', 'FIX_ZSLY.dat', 'FIX_ZWTN.dat'}
AWY_DATA = 'AWY.dat'
db = 'C:\\ProgramData\\Fenix\\Navdata\\nd.processed.db3'
src_db = 'C:\\ProgramData\\Fenix\\Navdata\\nd.db3.src'
conn = sqlite3.connect(db)
cur = conn.cursor()
#for dat in FIX_DATASET:
#    insert_fix(path_start + dat, cur, conn)
#insert_airports_and_runways(src_db, CIFP_PATH, cur, conn)
#insert_airways(path_start + AWY_DATA, cur, conn)
#insert_airwaylegs(path_start + AWY_DATA, cur, conn)
conn.close()
