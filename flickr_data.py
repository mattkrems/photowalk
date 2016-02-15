import flickrapi
import pandas as pd
import pymysql as mdb
import time
import utils

def get_comments(photo_id,flickr):
    comments=flickr.photos.comments.getList(photo_id=str(photo_id))
    if comments['comments'].get('comment') is None:
        num = 0
        comments = ''
    else:
        num = len(comments['comments']['comment'])
        comments = ' || '.join([x['_content'] for x in comments['comments']['comment']])
    print photo_id, num
    return num, comments

def get_num_favorites(photo_id,flickr):
    favs=flickr.photos.getFavorites(photo_id=str(photo_id))
    #num = len(favs['photo']['person'])
    num = favs['photo']['total']
    print photo_id, num
    return num

if __name__=='__main__':
    config = utils.get_config('config.ini')
    
    host = config['db']['host']
    user = config['db']['user']
    password = config['db']['password']
    db_name = config['db']['db']
    table_name = config['db']['table']
    api_key = config['flickr']['api_key']
    api_secret = config['flickr']['api_secret']    
    
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

    con = mdb.connect(host=host,user=user,password=password,db=db_name,charset='utf8mb4')
    cur = con.cursor()
    
    query = "SELECT id,num_comments,num_favs,comments FROM photos where location='sf' and date_taken between '2012-01-01' and NOW()"
    df = pd.read_sql(query,con)
    
    no_comment_photos = df[df.num_favs.isnull()]['id']
    
    for photo_id in no_comment_photos:
        try:
            #num_comments, comments = get_comments(photo_id,flickr)
            num_favs = get_num_favorites(photo_id,flickr)
            cur.execute('''UPDATE photos SET num_favs=%s WHERE id=%s''',(str(num_favs),str(photo_id)))
            #cur.execute('''UPDATE photos SET comments=%s WHERE id=%s''',(comments.encode('utf-8'),str(photo_id)))
            con.commit()
        except flickrapi.exceptions.FlickrError:
            continue
    
    
    
