import psycopg2
from config import config
from shapely import wkb
from pyproj import Proj, transform

sql_add_client = """INSERT INTO CLIENT(username,email,password) VALUES(%s,%s,%s) RETURNING id;"""
sql_add_log="""INSERT INTO LOG(username,action,details) VALUES(%s,%s,%s) RETURNING id;"""
sql_add_filters = """INSERT INTO FILTER(filters) VALUES(%s) RETURNING id;"""
#sql_TownStart = "select towns.geom, towns.name from towns "
#sql_townsBYregion = "inner join regions on st_contains(regions.geom, towns.geom) where regions.name="'%s'""
#sql_townByCoast = ""
#sql_TownEnd = ";"
sql_start = """WITH region_name AS (
    SELECT '{}'::TEXT AS name
),
region_towns AS (
    SELECT towns.name,towns.geom, towns.elevation, towns.nomos
    FROM towns 
    INNER JOIN regions ON ST_Contains(regions.geom, towns.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name
)"""
sql_medium=""" SELECT distinct region_towns.name, region_towns.geom, region_towns.elevation, region_towns.nomos
FROM region_towns {}"""
sql_river = "ST_DISTANCE(region_rivers.geom, region_towns.geom) < {}*1000"
sql_hospital = "ST_DISTANCE(region_hospitals.geom, region_towns.geom) < {}*1000"
sql_airport = "ST_DISTANCE(airports.geom, region_towns.geom) < {}*1000 "
sql_port = "ST_DISTANCE(region_ferryterminals.geom, region_towns.geom) < {}*1000 "
sql_coast = """ST_DISTANCE(region_aktogrammh.geom, region_towns.geom) < {}*1000 AND ST_DISTANCE(region_aktogrammh.geom, region_towns.geom) > {}*1000"""
sql_elevation = "region_towns.elevation <= {} AND region_towns.elevation >= {}"
sql_end = " FETCH FIRST 100 ROWS ONLY; """
sql_river2=""",
region_rivers AS(
	SELECT rivers.shape_leng,rivers.geom
    FROM rivers 
    INNER JOIN regions ON ST_Contains(regions.geom, rivers.geom) 
    CROSS JOIN region_name
    WHERE regions.name = region_name.name)"""
sql_hospital2=""",
region_hospitals AS (
    SELECT hospitals.geom 
    FROM hospitals 
    INNER JOIN regions ON ST_Contains(regions.geom, hospitals.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name)"""
sql_port2=""",
region_ferryterminals as(
    SELECT ferryterminals.geom 
    FROM ferryterminals 
    INNER JOIN regions ON ST_Contains(regions.geom, ferryterminals.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name)"""
sql_coast2=""",
region_aktogrammh as(
    SELECT aktogrammh.geom 
    FROM aktogrammh 
    INNER JOIN regions ON ST_Contains(regions.geom, aktogrammh.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name)"""
#check connection between flask and db
def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()
        
	# execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

#connection with db
def get_db_connection():
    conn = psycopg2.connect(
        host="postgres",
        database="postgres",
        user="postgres",
        password="1234")
    return conn
####TOWNS
def searchTowns(selectedRegion,rangeAirport,rangeCoastMax, rangeCoastMin,rangeHospital,rangePort, rangeRiver, rangeElevationMin, rangeElevationMax):
    thisSQL = sql_start.format(selectedRegion)
    sql_from = ""
    if(rangeCoastMin != 0 and rangeCoastMax != 0 ):
        thisSQL = thisSQL+sql_coast2
        sql_from = sql_from+", region_aktogrammh"
    if(rangeHospital != 0):
        thisSQL = thisSQL+sql_hospital2
        sql_from = sql_from+", region_hospitals" 
    if(rangeRiver != 0):
        thisSQL = thisSQL+sql_river2
        sql_from = sql_from+", region_rivers" 
    if(rangePort != 0):
        thisSQL = thisSQL+sql_port2
        sql_from = sql_from+", region_ferryterminals" 
    if(rangeAirport != 0):
        sql_from = sql_from+", airports" 
    thisSQL = thisSQL+sql_medium.format(sql_from)
    hasfilters = bool(False)
    if(rangeElevationMin != 0 and rangeElevationMax != 0 ):
        if(hasfilters):
           thisSQL = thisSQL+" and "+sql_elevation.format(rangeElevationMax, rangeElevationMin)
        else:
            thisSQL = thisSQL+" where "+ sql_elevation.format(rangeElevationMax, rangeElevationMin)
            hasfilters = bool(True)
    if(rangeAirport != 0):
        if(hasfilters):
           thisSQL = thisSQL+" and "+sql_airport.format(rangeAirport)
        else:
            thisSQL = thisSQL+" where "+ sql_airport.format(rangeAirport)
            hasfilters = bool(True)
    if(rangeCoastMin != 0 and rangeCoastMax != 0 ):
        if(hasfilters):
           thisSQL = thisSQL+" and "+sql_coast.format(rangeCoastMax, rangeCoastMin)
        else:
            thisSQL = thisSQL+" where "+sql_coast.format(rangeCoastMax, rangeCoastMin)
            hasfilters = bool(True)
    if(rangeRiver != 0):
        if(hasfilters):
           thisSQL = thisSQL+" and "+sql_river.format(rangeRiver)
        else:
            thisSQL = thisSQL+" where "+ sql_river.format(rangeRiver)
            hasfilters = bool(True)
    if(rangePort != 0):
        if(hasfilters):
           thisSQL = thisSQL+" and "+sql_port.format(rangePort)
        else:
            thisSQL = thisSQL+" where "+ sql_port.format(rangePort)
            hasfilters = bool(True)
    if(rangeHospital != 0):
        if(hasfilters):
           thisSQL = thisSQL+" and "+sql_hospital.format(rangeHospital)
        else:
            thisSQL = thisSQL+" where "+ sql_hospital.format(rangeHospital)
            hasfilters = bool(True)

    thisSQL = thisSQL+sql_end
    print(thisSQL)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(thisSQL)
        print('testttttttt2')
        towns = cur.fetchall()
        print('testttttttt3')
        cur.close()
        conn.close()
        print(towns)
        if(len(towns)>0):
            townPoints = hexToLatLong(towns)
            #townPoints = projected_to_degrees(townPoints)
            print(townPoints)
            response = townPoints
        else:
            response = {'message': 'Data not found'}
    except Exception as e:
        response = {'message': 'Bad request or connection error'}
    return response

def hexToLatLong(hexpoints):
    LatLongPoints = []
    proj_in = Proj(init='epsg:2100')
    proj_out = Proj(init='epsg:4326') 
    for point in hexpoints:
        name = point[0]
        elevation = point[2]
        county = point[3]
        geom = wkb.loads(point[1], hex=True)
        longitude, latitude = transform(proj_in, proj_out, geom.x, geom.y)
        LatLongPoints.append((f"{name},{latitude},{longitude},{elevation},{county}"))
    return LatLongPoints
#########TABLE LOG########
#get all logs
def get_all_logs():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM LOG ORDER BY date_created DESC;')
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return logs

#add log
def add_log(username,action,details):
    conn = get_db_connection()
    cur = conn.cursor()
    id = cur.execute(sql_add_log,(username,action,details))
    conn.commit()
    cur.close()
    conn.close()
    return id

#add filter
def add_filters(data):
    conn = get_db_connection()
    cur = conn.cursor()
    id = cur.execute(sql_add_filters,(data,))
    conn.commit()
    cur.close()
    conn.close()
    return id

#########TABLE CLIENT#############
#get all clients
def get_all_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CLIENT;')
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return clients

#get client info from id
def search_by_id(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CLIENT WHERE id=%s;',[id])
    client = cur.fetchall()
    cur.close()
    conn.close()
    return client[0]

#get client info from access
def search_by_access(access):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM CLIENT WHERE access=%s;',[access])
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return clients

#delete client
def delete_client(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM CLIENT WHERE id = %s;',[client_id])
    conn.commit()
    cur.close()
    conn.close()
    return

#add client
def add_client(username,email,password):
    conn = get_db_connection()
    cur = conn.cursor()
    id = cur.execute(sql_add_client,(username,email,password))
    conn.commit()
    cur.close()
    conn.close()
    return id

#updates client
def update_client(id,username,access,date_created,email,password):
    print(id,username,access,date_created,email,password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE CLIENT SET username = %s,access=%s,date_created=%s,\
        email=%s,password=%s WHERE id = %s;',[username,access,date_created,email,password,id])
    conn.commit()
    cur.close()
    conn.close()
    return

#main
if __name__ == '__main__':
    connect()