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
    SELECT '{}'::TEXT AS name),
region_towns AS (
    SELECT towns.name,towns.geom, towns.elevation, towns.nomos
    FROM towns 
    INNER JOIN regions ON ST_Contains(regions.geom, towns.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name),
region_aktogrammh as(
    SELECT aktogrammh.geom 
    FROM aktogrammh 
    INNER JOIN regions ON ST_Contains(regions.geom, aktogrammh.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name),
region_ferryterminals as(
    SELECT ferryterminals.geom 
    FROM ferryterminals 
    INNER JOIN regions ON ST_Contains(regions.geom, ferryterminals.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name),
region_hospitals AS (
    SELECT hospitals.geom 
    FROM hospitals 
    INNER JOIN regions ON ST_Contains(regions.geom, hospitals.geom) 
	CROSS JOIN region_name
    WHERE regions.name = region_name.name),
region_rivers AS(
	SELECT rivers.shape_leng,rivers.geom
    FROM rivers 
    INNER JOIN regions ON ST_Contains(regions.geom, rivers.geom) 
    CROSS JOIN region_name
    WHERE regions.name = region_name.name)
SELECT distinct region_towns.name, region_towns.geom, region_towns.elevation, region_towns.nomos,
    (SELECT MIN(ST_Distance(region_rivers.geom, region_towns.geom)) FROM region_rivers) AS min_distance_to_river,
    (SELECT MIN(ST_Distance(region_hospitals.geom, region_towns.geom)) FROM region_hospitals) AS min_distance_to_hospital,
    (SELECT MIN(ST_Distance(airports.geom, region_towns.geom)) FROM airports) AS min_distance_to_airport,
    (SELECT MIN(ST_Distance(region_ferryterminals.geom, region_towns.geom)) FROM region_ferryterminals) AS min_distance_to_port,
    (SELECT MIN(ST_Distance(region_aktogrammh.geom, region_towns.geom)) FROM region_aktogrammh) AS min_distance_to_coast
FROM region_towns, region_aktogrammh, region_hospitals, region_rivers, region_ferryterminals, airports """
sql_river = "ST_DISTANCE(region_rivers.geom, region_towns.geom) < {}*1000"
sql_hospital = "ST_DISTANCE(region_hospitals.geom, region_towns.geom) < {}*1000"
sql_airport = "ST_DISTANCE(airports.geom, region_towns.geom) < {}*1000 "
sql_port = "ST_DISTANCE(region_ferryterminals.geom, region_towns.geom) < {}*1000 "
sql_coast = """ST_DISTANCE(region_aktogrammh.geom, region_towns.geom) < {}*1000 AND ST_DISTANCE(region_aktogrammh.geom, region_towns.geom) > {}*1000"""
sql_elevation = "region_towns.elevation <= {} AND region_towns.elevation >= {}"
sql_end = " FETCH FIRST 100 ROWS ONLY; """
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
#get all logs
def get_all_athens_regions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id,geom,name,custom_hos,custom_sch,custom_sta,custom_slo,custom_coa,custom_dem,custom_pop,custom_wor FROM athens;')
    regions = cur.fetchall()
    cur.close()
    conn.close()
    return regions

def searchTowns(selectedRegion,rangeAirport,rangeCoastMax, 
                rangeCoastMin,rangeHospital,rangePort, rangeRiver, 
                rangeElevationMin, rangeElevationMax):
    thisSQL = sql_start.format(selectedRegion)
    thisSQL = thisSQL
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
    if(rangeCoastMax != 0 ):
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
        #print('testttttttt2')
        towns = cur.fetchall()
        cur.close()
        conn.close()
        #print(towns)
        if(len(towns)>0):
            townPoints = hexToLatLong(towns)
            #print(townPoints)
            response = townPoints
        else:
            response = {'message': 'Data not found'}
    except Exception as e:
        response = {'message': 'Bad request or connection error'}
    return response
def do_the_math(WDistance,WSpatial,WDemographic,WSchool,WHospital,WTransport,
                WSlope,WCoast,WElevation,WPopulation,WEconomy,regions):
    column_names = ['id', 'geom', 'name', 'custom_hos', 'custom_sch', 'custom_sta', 'custom_slo', 'custom_coa', 'custom_dem', 'custom_pop', 'custom_wor']
    Spatial=[]
    for i in range(0, len(regions)):
        Slope = regions[i][column_names.index('custom_slo')]
        Elevation = regions[i][column_names.index('custom_dem')]
        Coast = regions[i][column_names.index('custom_coa')]
        value = WSlope*Slope + WElevation*Elevation + WCoast*Coast
        Spatial.append(value)
    Demographic=[]
    for i in range(0, len(regions)):
        Population = regions[i][column_names.index('custom_pop')]
        Economy = regions[i][column_names.index('custom_wor')]
        value = WPopulation*Population + WEconomy*Economy
        Demographic.append(value)
    Distance=[]
    for i in range(0, len(regions)):
        School = regions[i][column_names.index('custom_sch')]
        Hospital = regions[i][column_names.index('custom_hos')]
        Transport = regions[i][column_names.index('custom_sta')]
        value = WSchool*School + WHospital*Hospital + WTransport*Transport
        Distance.append(value)
    final=[]
    for i in range(0, len(regions)):
        value= WSpatial*Spatial[i]+WDemographic*Demographic[i]+WDistance*Distance[i]
        final.append(value)
    id=[]
    name=[]
    geom=[]
    for i in range(0, len(regions)):
        value_id=regions[i][column_names.index('id')]
        value_name=regions[i][column_names.index('name')]
        value_geom=regions[i][column_names.index('geom')]
        id.append(value_id)
        name.append(value_name)
        geom.append(value_geom)
    response=[]
    for i in range(0, len(regions)):
        response.append((f"{id[i]},{geom[i]},{name[i]},{final[i]}"))
    return response

def hexToLatLong(hexpoints):
    LatLongPoints = []
    proj_in = Proj(init='epsg:2100')
    proj_out = Proj(init='epsg:4326') 
    for point in hexpoints:
        name = point[0]
        elevation = point[2]
        county = point[3]
        river = point[4]
        hospital = point[5]
        airport = point[6]
        port = point[7]
        coast = point[8]
        geom = wkb.loads(point[1], hex=True)
        longitude, latitude = transform(proj_in, proj_out, geom.x, geom.y)
        LatLongPoints.append((f"{name},{latitude},{longitude},{elevation},{county},{river},{hospital},{airport},{port},{coast}"))
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