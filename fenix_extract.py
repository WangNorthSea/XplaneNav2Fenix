import sqlite3

EXTRACT_SET = ['ZUKD']

def get_new_navaid_id(src_navaid_id, src_cursor, cursor):
    src_cursor.execute('SELECT Ident, Country, NavKeyCode FROM NavaidLookup WHERE ID = ?', (src_navaid_id,))
    src_navaidlookup_rec = src_cursor.fetchone()
    cursor.execute('SELECT ID FROM Navaids WHERE Ident = ? and Country = ?', (src_navaidlookup_rec[0], src_navaidlookup_rec[1]))
    navaidlookup_rec = cursor.fetchone()
    if navaidlookup_rec == None:
        src_cursor.execute('SELECT * FROM Navaids WHERE ID = ?', (src_navaid_id,))
        #insert into Navaids
        src_navaid_rec = src_cursor.fetchone()
        cursor.execute('''
            INSERT INTO Navaids (Ident, Type, Name, Freq, Channel, Usage, Latitude, Longtitude, Elevation, SlavedVar, 
                                MagneticVariation, Range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)            
        ''', (src_navaid_rec[1], src_navaid_rec[2], src_navaid_rec[3], src_navaid_rec[4], src_navaid_rec[5], src_navaid_rec[6],
                src_navaid_rec[7], src_navaid_rec[8], src_navaid_rec[9], src_navaid_rec[10], src_navaid_rec[11], src_navaid_rec[12]))
        
        #insert into NavaidLookup
        cursor.execute('SELECT COUNT(*) FROM Navaids')
        new_navaid_id = cursor.fetchone()[0]
        cursor.execute('''
            INSERT INTO NavaidLookup (Ident, Type, Country, NavKeyCode, ID)
            VALUES (?, ?, ?, ?, ?)
        ''', (src_navaid_rec[1], src_navaid_rec[2], src_navaidlookup_rec[1], src_navaidlookup_rec[2], new_navaid_id))
    else:
        new_navaid_id = navaidlookup_rec[0]
    return new_navaid_id

def get_new_wpt_id(src_wpt_id, src_cursor, cursor):
    src_cursor.execute('SELECT Ident, Country FROM WaypointLookup WHERE ID = ?', (src_wpt_id,))
    src_wptlookup_rec = src_cursor.fetchone()
    cursor.execute('SELECT ID FROM WaypointLookup WHERE Ident = ? and Country = ?', (src_wptlookup_rec[0], src_wptlookup_rec[1]))
    wpt_rec = cursor.fetchone()
    if wpt_rec == None:
        #insert new waypoint
        src_cursor.execute('SELECT * FROM Waypoints WHERE ID = ?', (src_wpt_id,))
        src_wpt_rec = src_cursor.fetchone()
        new_navaid_id = None
        if src_wpt_rec[6] != None:
            #has NavaidID
            new_navaid_id = get_new_navaid_id(src_wpt_rec[6], src_cursor, cursor)
        #insert into Waypoints
        cursor.execute('''
            INSERT INTO Waypoints (Ident, Collocated, Name, Latitude, Longtitude, NavaidID)
            VALUES (?, ?, ?, ?, ?, ?)            
        ''', (src_wpt_rec[1], src_wpt_rec[2], src_wpt_rec[3], src_wpt_rec[4], src_wpt_rec[5], new_navaid_id))
        
        #insert into WaypointLookup
        cursor.execute('SELECT COUNT(*) FROM Waypoints')
        new_wpt_id = cursor.fetchone()[0]
        cursor.execute('''
            INSERT INTO WaypointLookup (Ident, Country, ID)
            VALUES (?, ?, ?)
        ''', (src_wpt_rec[1], src_wptlookup_rec[1], new_wpt_id))
    else:
        new_wpt_id = wpt_rec[0]
    return new_wpt_id

def data_extract(icao_str, src_cursor, cursor):
    src_cursor.execute('SELECT * FROM Airports WHERE ICAO = ?', (icao_str,))
    apt_rec = src_cursor.fetchone()
    if apt_rec == None:
        print('Source database airport not found: ' + icao_str)
        return
    #insert into Airports and AirportLookup
    cursor.execute('SELECT COUNT(*) FROM Airports')
    new_apt_id = cursor.fetchone()[0] + 1
    cursor.execute('''
        INSERT INTO Airports (Name, ICAO, Latitude, Longtitude, Elevation, TransitionAltitude, 
                    TransitionLevel, SpeedLimit, SpeedLimitAltitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)            
    ''', (apt_rec[1], apt_rec[2], apt_rec[4], apt_rec[5], apt_rec[6], apt_rec[7], apt_rec[8], apt_rec[9], apt_rec[10]))
    cursor.execute('''
        INSERT INTO AirportLookup (extID, ID) VALUES (?, ?)
    ''', (icao_str[:2] + icao_str, new_apt_id))

    src_cursor.execute('SELECT * FROM Runways WHERE AirportID = ?', (apt_rec[0],))
    #insert into Runways
    rwy_ident_to_id = {}
    cursor.execute('SELECT COUNT(*) FROM Runways')
    new_rwy_id = cursor.fetchone()[0] + 1
    for rwy_rec in src_cursor.fetchall():
        cursor.execute('''
            INSERT INTO Runways (AirportID, Ident, TrueHeading, Length, Width, Surface, Latitude, Longtitude, Elevation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)            
        ''', (new_apt_id, rwy_rec[2], rwy_rec[3], rwy_rec[4], rwy_rec[5], rwy_rec[6], rwy_rec[7], rwy_rec[8], rwy_rec[9]))
        rwy_ident_to_id[rwy_rec[2]] = new_rwy_id
        new_rwy_id += 1

    #search Terminals
    src_cursor.execute('SELECT * FROM Terminals WHERE AirportID = ?', (apt_rec[0],))
    tmr_rec_set = src_cursor.fetchall()
    if tmr_rec_set == None:
        print('Source database no terminals for airport: ' + icao_str)
        return
    
    for tmr_rec in tmr_rec_set:
        if tmr_rec[6] != None:
            tmr_rwy_id = rwy_ident_to_id[tmr_rec[6]]
        else:
            tmr_rwy_id = None
        #check IlsID
        new_ils_id = None
        if tmr_rec[8] != None:
            src_cursor.execute('SELECT * FROM ILSes WHERE ID = ?', (tmr_rec[8],))
            ils_rec = src_cursor.fetchone()
            #insert into ILSes
            cursor.execute('''
                INSERT INTO ILSes (RunwayID, Freq, GsAngle, Latitude, Longtitude, Category, Ident, LocCourse, CrossingHeight,
                                    HasDme, Elevation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tmr_rwy_id, ils_rec[2], ils_rec[3], ils_rec[4], ils_rec[5], ils_rec[6], 
                  ils_rec[7], ils_rec[8], ils_rec[9], ils_rec[10], ils_rec[11]))
            cursor.execute('SELECT COUNT(*) FROM ILSes')
            new_ils_id = cursor.fetchone()[0]
        
        #insert into Terminals
        cursor.execute('''
            INSERT INTO Terminals (AirportID, Proc, ICAO, FullName, Name, Rwy, RwyID, IlsID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (new_apt_id, tmr_rec[2], tmr_rec[3], tmr_rec[4], tmr_rec[5], tmr_rec[6], tmr_rwy_id, new_ils_id))

        cursor.execute('SELECT COUNT(*) FROM Terminals')
        new_tmr_id = cursor.fetchone()[0]
        
        #search TerminalLegs
        src_cursor.execute('SELECT * FROM TerminalLegs WHERE TerminalID = ?', (tmr_rec[0],))
        tmr_leg_rec_set = src_cursor.fetchall()
        for tmr_leg_rec in tmr_leg_rec_set:
            #check wpt
            new_wpt_id = None
            if tmr_leg_rec[5] != None:
                new_wpt_id = get_new_wpt_id(tmr_leg_rec[5], src_cursor, cursor)
            #check navaid
            new_nav_id = None
            if tmr_leg_rec[9] != None:
                new_nav_id = get_new_navaid_id(tmr_leg_rec[9], src_cursor, cursor)
            #check center
            new_center_id = None
            if tmr_leg_rec[18] != None:
                new_center_id = get_new_wpt_id(tmr_leg_rec[18], src_cursor, cursor)

            #insert into TerminalLegs
            cursor.execute('''
                INSERT INTO TerminalLegs (TerminalID, Type, Transition, TrackCode, WptID, WptLat, WptLon, TurnDir,
                            NavID, NavLat, NavLon, NavBear, NavDist, Course, Distance, Alt, Vnav, CenterID, CenterLat, CenterLon, WptDescCode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (new_tmr_id, tmr_leg_rec[2], tmr_leg_rec[3], tmr_leg_rec[4], new_wpt_id, tmr_leg_rec[6], tmr_leg_rec[7], tmr_leg_rec[8],
                  new_nav_id, tmr_leg_rec[10], tmr_leg_rec[11], tmr_leg_rec[12], tmr_leg_rec[13], tmr_leg_rec[14], tmr_leg_rec[15], tmr_leg_rec[16],
                  tmr_leg_rec[17], new_center_id, tmr_leg_rec[19], tmr_leg_rec[20], tmr_leg_rec[21]))
                
            #insert into TerminalLegsEx
            src_cursor.execute('SELECT * FROM TerminalLegsEx WHERE ID = ?', (tmr_leg_rec[0],))
            src_tmrlegex_rec = src_cursor.fetchone()
            cursor.execute('''
                INSERT INTO TerminalLegsEx (IsFlyOver, SpeedLimit, SpeedLimitDescription)
                VALUES (?, ?, ?)      
            ''', (src_tmrlegex_rec[1], src_tmrlegex_rec[2], src_tmrlegex_rec[3]))


src_db = 'C:\\ProgramData\\Fenix\\Navdata\\nd.db3.src2'
db = 'C:\\ProgramData\\Fenix\\Navdata\\nd.processed.db3'
src_conn = sqlite3.connect(src_db)
conn = sqlite3.connect(db)
src_cur = src_conn.cursor()
cur = conn.cursor()
for apt in EXTRACT_SET:
    data_extract(apt, src_cur, cur)
conn.commit()
src_conn.close()
conn.close()
