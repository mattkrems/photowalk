import sqlalchemy
import pymysql as mdb
import pandas as pd
import sys
import utils
#turn off chained assignments warning in pandas 
pd.options.mode.chained_assignment = None

#this function creates the database
def create_db(con,cur,db_name,table_name):
    with con:
        cur.execute('''DROP TABLE IF EXISTS ''' + table_name)
        cur.execute('''CREATE TABLE ''' + table_name + '''(id BIGINT PRIMARY KEY,user_id VARCHAR(20),date_taken DATETIME,capture_device VARCHAR(100),title TEXT,user_tags TEXT,longitude DOUBLE,latitude DOUBLE,download_url VARCHAR(100),location VARCHAR(10))''') 
        cur.execute('''ALTER DATABASE ''' + db_name + ''' CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci''')
        cur.execute('''ALTER TABLE ''' + table_name + ''' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci''') 
        cur.execute('''ALTER TABLE ''' + table_name + ''' DEFAULT CHARACTER SET utf8mb4, MODIFY capture_device VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, MODIFY title TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, MODIFY user_tags TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;''')


def read_process_insert_data_file(filename,db_name,table_name,engine,locations):
    col_names=['id','user_id','date_taken','capture_device','title','user_tags','longitude','latitude','download_url','photo_or_video']

    #read in the file into a data frame by parts (each file has 10 million lines)
    num_lines_per_read=1000000
    parts=10
    for i in range(parts):
        df = pd.read_csv(filename,sep='\t',header=None,names=col_names,usecols=[0,1,3,5,6,8,10,11,14,22],nrows=num_lines_per_read,skiprows=i*num_lines_per_read)

        #get rid of all videos and photos with no location information
        df=df[(df.latitude.notnull()) & (df.photo_or_video==0)]
        df=df.drop('photo_or_video',1)

        for loc in locations:
            temp=df[(df.latitude>loc.miny) & (df.latitude<loc.maxy) & (df.longitude>loc.minx) & (df.longitude<loc.maxx)]
            temp['location'] = loc.name

            #insert into mysql database
            temp.to_sql(table_name,engine.raw_connection(),flavor='mysql',schema=db_name,index=False,if_exists='append')

class City(object):
    name=None    
    miny=None
    minx=None
    maxy=None
    maxx=None


if __name__=='__main__':
    config = utils.get_config('config.ini')
    
    host = config['db']['host']
    user = config['db']['user']
    password = config['db']['password']
    db_name = config['db']['db']
    table_name = config['db']['table']
    
    filename=sys.argv[1]

    con = mdb.connect(host=host,user=user,password=password,db=db_name,charset='utf8mb4')
    cur = con.cursor()
    #create_db(con,cur,db_name,table_name)
    
    city=City()
    city.name='sf'
    city.miny=37.7076
    city.maxy=37.8140
    city.minx=-122.5166
    city.maxx=-122.3544

    locations = [city]

    engine = sqlalchemy.create_engine('mysql+pymysql://' + user + ':' + password + '@' + host + '/' + db_name)
    read_process_insert_data_file(filename,db_name,table_name,engine,locations)






























    

