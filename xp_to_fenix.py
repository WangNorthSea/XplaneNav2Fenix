import sqlite3

def insert_fix(fix_file, cursor, connect):
    # Read data from file A and insert into Waypoints table
    with open(fix_file, 'r') as file:
        for line in file:
            # Parse the line to extract relevant information
            parts = line.strip().split()
            latitude = float(parts[0])
            longitude = float(parts[1])
            ident = parts[2]  # Correct index for 'Ident'
            name = ''.join(parts[6:])  # Combine the remaining parts as Name

            # Insert the data into the Waypoints table
            cursor.execute('''
                INSERT INTO Waypoints (Ident, Collocated, Name, Latitude, Longtitude)
                VALUES (?, ?, ?, ?, ?);
            ''', (ident, False, name, latitude, longitude))
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


db = 'nd.db3'
conn = sqlite3.connect(db)
cur = conn.cursor()
#insert_fix('E:\导航数据\FIX_ZWTN.dat', cur, conn)
insert_airways('E:\导航数据\AWY.dat', cur, conn)
conn.close()
