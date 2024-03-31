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
    wp1_id = cursor.fetchone()[0]
    cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country = ?', (wp2, wp2_country))
    wp2_id = cursor.fetchone()[0]
    cursor.execute('SELECT ID FROM Airways WHERE Ident = ?', (awy,)) #the comma can not be ignored
    awy_id = cursor.fetchone()[0]
    if dir == 'F':
        leg = AirwayLeg(awy_id, lvl, wp1_id, wp2_id)
        idx = (leg.awy_id, leg.wp1_id, leg.wp2_id)
        if legmap.get(idx) == None:
            legmap[idx] = leg
            if legSrcMap.get((leg.awy_id, leg.wp1_id)) == None:
                legSrcMap[(leg.awy_id, leg.wp1_id)] = set()
            legSrcMap[(leg.awy_id, leg.wp1_id)].add(leg)

            if legDestMap.get((leg.awy_id, leg.wp2_id)) == None:
                legDestMap[(leg.awy_id, leg.wp2_id)] = set()
            legDestMap[(leg.awy_id, leg.wp2_id)].add(leg)

            if legSrcMap.get((leg.awy_id, leg.wp2_id)) != None:
                for leg_itr in legSrcMap[(leg.awy_id, leg.wp2_id)]:
                    if leg_itr.wp2_id != leg.wp1_id:
                        leg_itr.prev = leg
                        leg.succ = leg_itr
            if legDestMap.get((leg.awy_id, leg.wp1_id)) != None:
                for leg_itr in legDestMap[(leg.awy_id, leg.wp1_id)]:
                    if leg_itr.wp1_id != leg.wp2_id:
                        leg_itr.succ = leg
                        leg.prev = leg_itr
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
            if legSrcMap.get((leg1.awy_id, leg1.wp1_id)) == None:
                legSrcMap[(leg1.awy_id, leg1.wp1_id)] = set()
            legSrcMap[(leg1.awy_id, leg1.wp1_id)].add(leg1)

            if legDestMap.get((leg1.awy_id, leg1.wp2_id)) == None:
                legDestMap[(leg1.awy_id, leg1.wp2_id)] = set()
            legDestMap[(leg1.awy_id, leg1.wp2_id)].add(leg1)

            if legSrcMap.get((leg1.awy_id, leg1.wp2_id)) != None:
                for leg_itr in legSrcMap[(leg1.awy_id, leg1.wp2_id)]:
                    if leg_itr.wp2_id != leg1.wp1_id:
                        leg_itr.prev = leg1
                        leg1.succ = leg_itr
            if legDestMap.get((leg1.awy_id, leg1.wp1_id)) != None:
                for leg_itr in legDestMap[(leg1.awy_id, leg1.wp1_id)]:
                    if leg_itr.wp1_id != leg1.wp2_id:
                        leg_itr.succ = leg1
                        leg1.prev = leg_itr
        else:
            if legmap[idx1].level != leg1.level:
                legmap[idx1].level = 'B'
        if legmap.get(idx2) == None:
            legmap[idx2] = leg2
            if legSrcMap.get((leg2.awy_id, leg2.wp1_id)) == None:
                legSrcMap[(leg2.awy_id, leg2.wp1_id)] = set()
            legSrcMap[(leg2.awy_id, leg2.wp1_id)].add(leg2)

            if legDestMap.get((leg2.awy_id, leg2.wp2_id)) == None:
                legDestMap[(leg2.awy_id, leg2.wp2_id)] = set()
            legDestMap[(leg2.awy_id, leg2.wp2_id)].add(leg2)

            if legSrcMap.get((leg2.awy_id, leg2.wp2_id)) != None:
                for leg_itr in legSrcMap[(leg2.awy_id, leg2.wp2_id)]:
                    if leg_itr.wp2_id != leg2.wp1_id:
                        leg_itr.prev = leg2
                        leg2.succ = leg_itr
            if legDestMap.get((leg2.awy_id, leg2.wp1_id)) != None:
                for leg_itr in legDestMap[(leg2.awy_id, leg2.wp1_id)]:
                    if leg_itr.wp1_id != leg2.wp2_id:
                        leg_itr.succ = leg2
                        leg2.prev = leg_itr
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
                cursor.execute('SELECT ID FROM Airports WHERE ICAO = ?', (icao_string,))
                if cursor.fetchone() == None:
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
                                    cursor.execute('''
                                        INSERT INTO AirportLookup (extID, ID) VALUES (?, ?)
                                    ''', (icao_string[:2] + icao_string, apt_id_start))
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
                    cursor.execute('''
                        INSERT INTO AirportLookup (extID, ID) VALUES (?, ?)
                    ''', (icao_string[:2] + icao_string, apt_id_start))
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

def insert_navaids(nav_file, cursor, connect):
    #Navaids, NavaidLookup, ILSes, Waypoints, WaypointLookup
    # 2 - NDB, 3 - VOR, 4 - ILS, 15 - GLS
    nav_map = {3:[4, 'T'], 2:[5, 'H'], 4:[8, 'H'], 15:[-1, '']}
    cursor.execute('SELECT COUNT(*) FROM Navaids')
    nav_id_start = cursor.fetchone()[0] + 1
    cursor.execute('SELECT COUNT(*) FROM ILSes')
    ils_id_start = cursor.fetchone()[0] + 1
    cursor.execute('SELECT COUNT(*) FROM Waypoints')
    wpt_id_start = cursor.fetchone()[0] + 1
    with open(nav_file, 'r') as file:
        last_ident = None
        for line in file:
            line_data = line.strip().split()
            row_code = int(line_data[0])
            lat_float = float(line_data[1])
            lon_float = float(line_data[2])
            elevation = int(line_data[3])
            freq_str = line_data[4]
            range = int(line_data[5])
            course_num = float(line_data[6])
            ident = line_data[7]
            icao_str = line_data[8]
            country = line_data[9]

            if nav_map.get(row_code) == None:
                if ident == last_ident and line_data[-1] == 'GS':
                    cursor.execute('UPDATE ILSes SET GsAngle = ? WHERE ID = ?', (float(line_data[6][:3]) / 100, ils_id_start - 1))
                continue

            type = nav_map[row_code][0]
            usage = nav_map[row_code][1]

            rwy_str = None
            if type == 8:
                rwy_str = line_data[10]
                cursor.execute('SELECT Name FROM Airports WHERE ICAO = ?', (icao_str,))
                apt_select = cursor.fetchone()
                if apt_select == None:
                    continue #ZULZ, no data for it
                name = apt_select[0]
            elif type == -1:
                rwy_str = 'RW' + line_data[10]
            else:
                name = ''
                for name_str in line_data[10:-1]:
                    name += name_str

            freq = 0
            left_move = 24
            for number in freq_str:
                freq += int(number) << left_move
                left_move -= 4

            #check if existed
            cursor.execute('SELECT COUNT(*) FROM NavaidLookup WHERE Ident = ? and Type = ? and Country = ?', (ident, type, country))
            if cursor.fetchone()[0] != 0:
                continue

            #get VOR SlavedVar
            slaved_var = 0
            if type == 4:
                slaved_var = course_num

            if type == 4 or type == 5 or type == 8:
                cursor.execute('''
                    INSERT INTO Navaids (Ident, Type, Name, Freq, Usage, Latitude, Longtitude, Elevation,
                            SlavedVar, MagneticVariation, Range)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)            
                ''', (ident, type, name, freq, usage, lat_float, lon_float, elevation, slaved_var, 0, range))

                cursor.execute('''
                    INSERT INTO NavaidLookup (Ident, Type, Country, NavKeyCode, ID)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ident, type, country, 1, nav_id_start))

                cursor.execute('''
                    INSERT INTO Waypoints (Ident, Collocated, Name, Latitude, Longtitude, NavaidID)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ident, True, name, lat_float, lon_float, nav_id_start))

                cursor.execute('''
                    INSERT INTO WaypointLookup (Ident, Country, ID)
                    VALUES(?, ?, ?)          
                ''', (ident, country, wpt_id_start))

                if type == 8:
                    #get runway id
                    cursor.execute('SELECT ID FROM Airports WHERE ICAO = ?', (icao_str,))
                    apt_id = cursor.fetchone()[0]
                    cursor.execute('SELECT ID FROM Runways WHERE AirportID = ? and Ident = ?', (apt_id, rwy_str))
                    rwy_id = cursor.fetchone()[0]
                    #insert into table ILSes
                    rwy_str = rwy_str[:2]
                    mag_course = course_num // 360
                    cursor.execute('''
                        INSERT INTO ILSes (RunwayID, Freq, GsAngle, Latitude, Longtitude, Category, Ident, LocCourse,
                                CrossingHeight, HasDme, Elevation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)            
                    ''', (rwy_id, freq, 3, lat_float, lon_float, 1, ident, mag_course, 50, True, elevation))
                    ils_id_start += 1
                nav_id_start += 1
                wpt_id_start += 1
            else:
                #EEU is for East Europe and China
                area_code = 'EEU'
                channel = int(freq_str)
                bearing = float(line_data[6][-7:])
                slope = float(line_data[6][:3]) / 100
                cursor.execute('''
                    INSERT INTO Gls (area_code, airport_identifier, icao_code, gls_ref_path_identifier, gls_category, gls_channel,
                                    runway_identifier, gls_approach_bearing, station_latitude, station_longitude, gls_station_ident,
                                    gls_approach_slope, magnetic_variation, station_elevation, station_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)      
                ''', (area_code, icao_str, country, ident, 1, channel, rwy_str, bearing, lat_float, lon_float, icao_str, slope, 0, elevation, ''))

            last_ident = ident
        connect.commit()

def insert_terminals(data_path, cursor, connect):
    #remember to check repeat procedure
    proc_map = {'STAR':1, 'SID':2, 'APPCH':3}
    cursor.execute('SELECT COUNT(*) FROM Terminals')
    tmr_id = cursor.fetchone()[0]
    for root, dirs, files in os.walk(data_path):
        for file in files:
            icao_string = file[:-4]
            with open(data_path + file, 'r') as tmr_lines:
                cursor.execute('SELECT ID FROM Airports WHERE ICAO = ?', (icao_string,))
                apt_id = cursor.fetchone()[0]
                inserted_proc = {}
                last_error_name = None
                rwy_to_wpt_id = {}
                for line in tmr_lines:
                    tmr_data = line.strip().split(',')
                    name = tmr_data[2]
                    #check if error happened
                    if last_error_name == name:
                        continue
                    rwy = 'ALL'
                    transition = ''
                    if tmr_data[0][:3] == 'SID':
                        proc = proc_map['SID']
                        if tmr_data[3].__contains__(' ') == False and tmr_data[3][:2] == 'RW':
                            rwy = tmr_data[3][2:]
                            transition = tmr_data[3]
                            if rwy[-1] == 'B':
                                rwy = 'ALL'
                                transition = 'ALL'
                    elif tmr_data[0][:4] == 'STAR':
                        proc = proc_map['STAR']
                        if tmr_data[3].__contains__(' ') == False and tmr_data[3][:2] == 'RW':
                            rwy = tmr_data[3][2:]
                            transition = tmr_data[3]
                            if rwy[-1] == 'B':
                                rwy = 'ALL'
                                transition = 'ALL'
                    elif tmr_data[0][:5] == 'APPCH':
                        proc = proc_map['APPCH']
                        rwy = name[1:4]
                        if rwy[-1] == '-':
                            rwy = rwy[:-1]
                        if tmr_data[3].__contains__(' ') == False:
                            transition = tmr_data[3]
                    else:
                        continue
                    
                    if inserted_proc.get(name) == None:
                        inserted_proc[name] = True
                        #check if repeated
                        cursor.execute('SELECT COUNT(*) FROM Terminals WHERE AirportID = ? and Name = ?', (apt_id, name))
                        if cursor.fetchone()[0] != 0:
                            continue
                        
                        #search RwyID
                        rwy_id = None
                        if rwy != 'ALL':
                            cursor.execute('SELECT ID FROM Runways WHERE AirportID = ? and Ident = ?', (apt_id, rwy))
                            rwy_rec = cursor.fetchone()
                            if rwy_rec == None:
                                print(icao_string)
                                print(tmr_data)
                            rwy_id = rwy_rec[0]

                        #search IlsID
                        IlsID = None
                        if proc == proc_map['APPCH'] and name[0] == 'I':
                            cursor.execute('SELECT ID FROM ILSes WHERE RunwayID = ?', (rwy_id,))
                            ils_rec = cursor.fetchone()
                            if ils_rec != None:
                                IlsID = ils_rec[0]

                        #insert into terminals
                        cursor.execute('''
                            INSERT INTO Terminals (AirportID, Proc, ICAO, FullName, Name, Rwy, RwyID, IlsID)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (apt_id, proc, icao_string, name, name, rwy, rwy_id, IlsID))
                        tmr_id += 1

                    type = tmr_data[1]
                    track_code = tmr_data[11]
                    wpt_ident = tmr_data[4]
                    country = tmr_data[5]

                    wpt_id = None
                    wpt_lat = None
                    wpt_lon = None
                    if wpt_ident.__contains__(' ') == False:
                        #search WptID
                        if wpt_ident[:2] == 'RW':
                            if rwy_to_wpt_id.get(wpt_ident) != None:
                                cursor.execute('SELECT ID, Latitude, Longtitude FROM Waypoints WHERE ID = ?', (rwy_to_wpt_id[wpt_ident],))
                                wpt_rec = cursor.fetchone()
                            else:
                                wpt_rec = None
                        else:
                            cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country = ?', (wpt_ident, country))
                            wpt_rec = cursor.fetchone()
                            if wpt_rec == None:
                                cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country like ?', (wpt_ident, country[0] + '%'))
                                wpt_rec = cursor.fetchone()
                        if wpt_rec == None and wpt_ident[:2] == 'RW':
                            #search Runway Latitude and Longtitude
                            cursor.execute('SELECT Latitude, Longtitude FROM Runways WHERE AirportID = ? and Ident = ?', (apt_id, rwy))
                            rwy_rec = cursor.fetchone()
                            wpt_lat, wpt_lon = rwy_rec[0], rwy_rec[1]

                            cursor.execute('SELECT COUNT(*) FROM Waypoints')
                            new_wpt_id = cursor.fetchone()[0] + 1
                            cursor.execute('''
                                INSERT INTO Waypoints (Ident, Collocated, Name, Latitude, Longtitude)
                                VALUES (?, ?, ?, ?, ?)            
                            ''', (wpt_ident, False, wpt_ident, wpt_lat, wpt_lon))
                            cursor.execute('''
                                INSERT INTO WaypointLookup (Ident, Country, ID)
                                VALUES (?, ?, ?)         
                            ''', (wpt_ident, country, new_wpt_id))
                            wpt_id = new_wpt_id
                            rwy_to_wpt_id[wpt_ident] = new_wpt_id
                        else:
                            if wpt_rec == None:
                                print('Error, this CIFP data contains waypoint not in database, ignored!')
                                print(icao_string + '.dat')
                                print(tmr_data)
                                cursor.execute('DELETE FROM TerminalLegsEx WHERE ID IN (SELECT ID FROM TerminalLegs WHERE TerminalID = ?)', (tmr_id,))
                                cursor.execute('DELETE FROM TerminalLegs WHERE TerminalID = ?', (tmr_id,))
                                cursor.execute('DELETE FROM Terminals WHERE ID = ?', (tmr_id,))
                                tmr_id -= 1
                                last_error_name = name
                                continue
                            wpt_id = wpt_rec[0]
                            #search WptLat, WptLon
                            cursor.execute('SELECT Latitude, Longtitude FROM Waypoints WHERE ID = ?', (wpt_id,))
                            wpt_rec = cursor.fetchone()
                            wpt_lat, wpt_lon = wpt_rec[0], wpt_rec[1]

                    turn_dir = None
                    if tmr_data[9].__contains__(' ') == False:
                        turn_dir = tmr_data[9]
                    
                    nav_id = None
                    nav_lat = None
                    nav_lon = None
                    nav_bear = None
                    nav_dist = None
                    if tmr_data[13].__contains__(' ') == False:
                        nav_ident = tmr_data[13]
                        nav_country = tmr_data[14]
                        #search NavID, NavLat, NavLon
                        cursor.execute('SELECT ID FROM NavaidLookup WHERE Ident = ? and Country = ?', (nav_ident, nav_country))
                        nav_rec = cursor.fetchone()
                        if nav_rec == None:
                            print('Error, this CIFP data contains navaid not in database, ignored!')
                            print(icao_string + '.dat')
                            print(tmr_data)
                        else:
                            nav_id = nav_rec[0]
                            cursor.execute('SELECT Latitude, Longtitude FROM Navaids WHERE ID = ?', (nav_id,))
                            nav_rec = cursor.fetchone()
                            nav_lat, nav_lon = nav_rec[0], nav_rec[1]
                            if tmr_data[18].__contains__(' ') == False:
                                nav_bear = float(tmr_data[18]) / 10
                            if tmr_data[19].__contains__(' ') == False:
                                nav_dist = float(tmr_data[19]) / 10
                    
                    course = None
                    if tmr_data[20].__contains__(' ') == False:
                        course = float(tmr_data[20]) / 10
                    
                    distance = None
                    if tmr_data[21].__contains__(' ') == False and tmr_data[21][0] != 'T':
                        distance = float(tmr_data[21]) / 10

                    alt_suffix = None
                    if tmr_data[22].__contains__(' ') == False:
                        alt_suffix = tmr_data[22]

                    alt = None
                    if tmr_data[23].__contains__(' ') == False:
                        alt = tmr_data[23]
                        while len(alt) < 5:
                            alt = '0' + alt
                        if alt_suffix == '+':
                            alt += 'A'
                        elif alt_suffix == '-':
                            alt += 'B'

                    vnav = None
                    if tmr_data[28].__contains__(' ') == False:
                        vnav = float(tmr_data[28]) * -1 / 100

                    center_ident = None
                    center_id = None
                    center_lat = None
                    center_lon = None
                    if tmr_data[30].__contains__(' ') == False:
                        center_ident = tmr_data[30]
                        center_country = tmr_data[31]
                        #search CenterID
                        if center_ident != icao_string:
                            cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country = ?', (center_ident, center_country))
                            center_rec = cursor.fetchone()
                            if center_rec == None:
                                print(icao_string)
                                print(tmr_data)
                                print(center_ident + ' ' + center_country)
                            center_id = center_rec[0]
                            #search CenterLat, CenterLon
                            cursor.execute('SELECT Latitude, Longtitude FROM Waypoints WHERE ID = ?', (center_id,))
                            center_rec = cursor.fetchone()
                            center_lat, center_lon = center_rec[0], center_rec[1]

                    wpt_desc_code = tmr_data[8]
                    is_fly_over = False
                    if wpt_desc_code[1] == 'Y':
                        is_fly_over = True
                        if wpt_desc_code[3] == 'M':
                            alt = 'MAP'

                    spd_limit_desc = None
                    spd_limit = None
                    if tmr_data[26] == '-':
                        spd_limit_desc = 'B'
                    elif tmr_data[26] == '+':
                        spd_limit_desc = 'A'

                    if tmr_data[27].__contains__(' ') == False:
                        spd_limit = float(tmr_data[27])

                    #insert into TerminalLegs and TerminalLegsEx
                    cursor.execute('''
                        INSERT INTO TerminalLegs (TerminalID, Type, Transition, TrackCode, WptID, WptLat, WptLon, 
                                    TurnDir, NavID, NavLat, NavLon, NavBear, NavDist, Course, 
                                    Distance, Alt, Vnav, CenterID, CenterLat, CenterLon, WptDescCode)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)            
                    ''', (tmr_id, type, transition, track_code, wpt_id, wpt_lat, wpt_lon, turn_dir,
                          nav_id, nav_lat, nav_lon, nav_bear, nav_dist, course, distance, alt, vnav,
                          center_id, center_lat, center_lon, wpt_desc_code))
                    
                    cursor.execute('''
                        INSERT INTO TerminalLegsEx (IsFlyOver, SpeedLimit, SpeedLimitDescription)
                        VALUES (?, ?, ?)            
                    ''', (is_fly_over, spd_limit, spd_limit_desc))
        connect.commit()


path_start = 'E:\\导航数据\\'
CIFP_PATH = path_start + 'CIFP\\'
FIX_DATASET = {'FIX.dat', 'FIX_ZPJH.dat', 'FIX_ZPLJ.dat', 'FIX_ZPMS.dat', 'FIX_ZSLY.dat', 'FIX_ZWTN.dat'}
NAV_DATA = 'NAV.dat'
AWY_DATA = 'AWY.dat'
db = 'C:\\ProgramData\\Fenix\\Navdata\\nd.processed.db3'
src_db = 'C:\\ProgramData\\Fenix\\Navdata\\nd.db3.src'
conn = sqlite3.connect(db)
cur = conn.cursor()
for dat in FIX_DATASET:
    insert_fix(path_start + dat, cur, conn)
insert_airports_and_runways(src_db, CIFP_PATH, cur, conn)
insert_navaids(path_start + NAV_DATA, cur, conn)
insert_airways(path_start + AWY_DATA, cur, conn)
insert_airwaylegs(path_start + AWY_DATA, cur, conn)
insert_terminals(CIFP_PATH, cur, conn)
conn.close()
