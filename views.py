from flask import Flask
app = Flask(__name__)

from flask import render_template, request
import cPickle as pickle
import pymysql as mdb
import pandas as pd
from retrying import retry
import geocoder
import ConfigParser
import osmnx_utils as ou
import utils

config = utils.get_config('config.ini')    
default_center = '37.77709, -122.44623'
default_start = 'Palace of Fine Arts, San Francisco, CA'
default_end = 'Coit Tower, San Francisco, CA'
sg=pickle.load(open( "sf_complete.pkl", "r" ))
    
@app.route('/')
@app.route('/index')
def input():
    return render_template("input.html",center_coords=default_center,zoom=13,
                           default_start=default_start, default_end=default_end)

@app.errorhandler(404)
def pageNotFound(error):
    print "ERROR"
    print error
    return render_template("error.html",center_coords=default_center,zoom=13,
                           error = 'error: please try again',
                           default_start=default_start, default_end=default_end) 

@app.errorhandler(500)
def internal_error(error):
    print "ERROR"
    print error
    return render_template("error.html",center_coords=default_center,zoom=13,
                           error = 'error: please try again',
                           default_start=default_start, default_end=default_end)     

@app.route('/about')
def about():
    return render_template("about.html")

    
@app.route('/output')
def output():
    start = request.args.get('start')
    end = request.args.get('end')
    routetype = request.args.get('routetype')
    
    if routetype == "Slow":
        alpha=8
        slow="selected"
        medium=""
        fast=""
    elif routetype == "Medium":
        alpha=4
        slow=""
        medium="selected"
        fast=""
    elif routetype == "Fast":
        alpha=1
        slow=""
        medium=""
        fast="selected"

    pos0,pos1 = process_input(start,end)

    print pos0, pos1, alpha
    
    # show error pages if any of the points cannot be found
    if pos0 is None:
        return render_template("error.html",center_coords=default_center,zoom=13,
                                error = 'error: cannot find ' + start,
                                default_start=default_start, default_end=default_end)
    elif pos1 is None:
        return render_template("error.html",center_coords=default_center,zoom=13,
                                error = 'error: cannot find ' + end,
                                default_start=default_start, default_end=default_end)

    # get path info
    try:
        slinepath,sdistance,plinepath,pdistance = ou.get_graph_info_for_web(sg,pos0,pos1,alpha=alpha)
    except:
        return render_template("error.html",center_coords=default_center,zoom=13,
                                error = 'error: no map data here, please try different locations',
                                default_start=default_start, default_end=default_end) 
    
    print sdistance,pdistance
    # get path in form usable for javascript
    ppath = [list(a) for a in zip(plinepath[:,1],plinepath[:,0])]
    spath = [list(a) for a in zip(slinepath[:,1],slinepath[:,0])]
    
    links_and_points=get_photos_along_path(ppath,8)

    # calculate new center position
    new_center_lat = (pos0[0]+pos1[0])/2
    new_center_lon = (pos0[1]+pos1[1])/2
    center_coords = str(new_center_lat) + ',' + str(new_center_lon)
    
    if pdistance < 3:
        zoom = 15
    elif 3 <= pdistance <= 6:
        zoom = 14
    elif pdistance > 6:
        zoom = 13 
    
    return render_template("output.html",center_coords=center_coords,zoom=zoom,
                           start_name = start,
                           startlat = str(ppath[0][0]),
                           startlon = str(ppath[0][1]),
                           end_name = end,
                           endlat = str(ppath[-1][0]),
                           endlon = str(ppath[-1][1]),
                           plinepath = ppath,
                           #slinepath = spath,
                           image_points = links_and_points,
                           start_val=start,
                           end_val=end,
                           slow=slow,
                           medium=medium,
                           fast=fast,
                           pdistance=str.format('{0:.2f}',pdistance),
                           sdistance=str.format('{0:.2f}',sdistance))

@retry(stop_max_attempt_number=10)
def process_input(start,end):
    start_loc = geocoder.google(start)
    end_loc = geocoder.google(end)
    
    print start_loc
    print end_loc
    
    if not start_loc.ok:
        return None, None
    elif not end_loc.ok:
        return start_loc.latlng, None
    else:
        return start_loc.latlng,end_loc.latlng

        
def get_photos_along_path(path,num_points):
    con = mdb.connect(host=config['db']['host'],user=config['db']['user'],password=config['db']['password'],db=config['db']['db'],charset='utf8mb4')
    cur = con.cursor()
    tolerance = 0.001   
    points = ou.get_points_along_path(path,num_points)
    
    photos = []
    latlons = []
    for point in points:
        minlat = str(point[0]-tolerance)
        maxlat = str(point[0]+tolerance)
        minlon = str(point[1]-tolerance)
        maxlon = str(point[1]+tolerance)
    
        query = "SELECT download_url,latitude,longitude,num_favs,num_comments,views FROM photos where location='sf' and latitude between " + minlat + " and " + maxlat + " and longitude between " + minlon + " and " + maxlon + " and (auto_tags like '%outdoor%')"
        df = pd.read_sql(query,con)
        print df.shape
        try:
            sample = df.sample()
            sample = df.head(1)
        except:
            continue

        sample_url = sample.download_url.values[0]
        sample_lat = sample.latitude.values[0]
        sample_lon = sample.longitude.values[0]
        print sample_url,sample_lat,sample_lon
              
        photos.append(sample_url)
        latlons.append(str(sample_lat) + ',' + str(sample_lon))
    con.close()
    return zip(photos,latlons)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='0.0.0.0', port=80, debug=False)
