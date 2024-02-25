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


path_start = 'E:\\导航数据\\'
FIX_DATASET = {'FIX.dat', 'FIX_ZPJH.dat', 'FIX_ZPLJ.dat', 'FIX_ZPMS.dat', 'FIX_ZSLY.dat', 'FIX_ZWTN.dat'}
AWY_DATA = 'AWY.dat'
db = "C:\\ProgramData\\Fenix\\Navdata\\nd.processed.db3"
conn = sqlite3.connect(db)
cur = conn.cursor()
#for dat in FIX_DATASET:
#    insert_fix(path_start + dat, cur, conn)
#insert_airways(path_start + AWY_DATA, cur, conn)
insert_airwaylegs(path_start + AWY_DATA, cur, conn)
conn.close()
