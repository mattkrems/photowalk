import numpy as np
import math
import pandas as pd
import json
import networkx as nx

def get_edge_weights(sg,model=None):
    #i=0
    for n0, n1 in sg.edges_iter():
        #if i%1000 == 0: print "edge: ", i
        #i = i + 1
        path = get_path(n0, n1,sg)       
        distance = get_path_length(path)
        sg.edge[n0][n1]['distance'] = distance       
        if model != None:
            density = get_path_density(path,model)
            sg.edge[n0][n1]['density'] = density
            
def get_edge_photo_weights(sg,model):
    i=0
    for n0, n1 in sg.edges_iter():
        if i%1000 == 0: print "edge: ", i
        i = i + 1
        path = get_path(n0, n1,sg)            
        density = get_path_density(path,model)
        sg.edge[n0][n1]['density'] = density

def get_photolength(sg,alpha=1):
    for n0,n1 in sg.edges_iter():
        #sg.edge[n0][n1]['photolength'] = sg.edge[n0][n1]['distance']*(1/(1+np.exp(alpha*sg.edge[n0][n1]['density'])))
        density = sg[n0][n1]['density']
        if density < 0: density=0
        sg.edge[n0][n1]['photolength'] = sg.edge[n0][n1]['distance']*(1/(1+np.power(density,alpha)))

def get_path(n0,n1,sg):
    """If n0 and n1 are connected nodes in the graph, this function
    return an array of point coordinates along the road linking
    these two nodes."""
    return np.array(json.loads(sg[n0][n1]['Json'])['coordinates'])

def get_path_length(path):
    #return np.sum(geocalc(path[1:,0],path[1:,1],path[:-1,0],path[:-1,1]))
    return np.sum(geocalc(path[1:,1],path[1:,0],path[:-1,1],path[:-1,0]))

def get_path_density(path,model=None):
    #return np.sum(densitycalc(path[1:,0],path[1:,1],path[:-1,0],path[:-1,1],model))
    return np.sum(densitycalc(path[1:,1],path[1:,0],path[:-1,1],path[:-1,0],model))

#for now just sample along straight line between endpoints                      
def get_path_density2(path,distance,model):
    lat0 = path[0][1]
    lon0 = path[0][0]
    lat1 = path[-1][1]
    lon1 = path[-1][0]
    return densitycalc2(lat0,lon0,lat1,lon1,distance,model)
                         
EARTH_R = 3959
def geocalc(lat0,lon0,lat1,lon1):
    #print "geocalc: ",lat0, lon0, lat1, lon1
    """Return the distance (in km) between two points in 
    geographical coordinates."""
    lat0 = np.radians(lat0)
    lon0 = np.radians(lon0)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    dlon = lon0 - lon1
    y = np.sqrt(
        (np.cos(lat1) * np.sin(dlon)) ** 2
         + (np.cos(lat0) * np.sin(lat1) 
         - np.sin(lat0) * np.cos(lat1) * np.cos(dlon)) ** 2)
    x = np.sin(lat0) * np.sin(lat1) + \
        np.cos(lat0) * np.cos(lat1) * np.cos(dlon)
    c = np.arctan2(y, x)
    return EARTH_R * c

def densitycalc(lat1,lon1,lat2,lon2,model=None):
    #print "densitycalc: ",lat1,lon1,lat2,lon2
    #get midpoint of the edge section   
    lat1,lon1 = np.radians(lat1), np.radians(lon1)
    lat2,lon2 = np.radians(lat2), np.radians(lon2)
    dLon = lon2-lon1
    Bx = np.cos(lat2) * np.cos(dLon)
    By = np.cos(lat2) * np.sin(dLon)
    lat3 = np.arctan2(np.sin(lat1)+np.sin(lat2), np.sqrt((np.cos(lat1)+Bx)*(np.cos(lat1)+Bx) + By*By))
    lon3 = lon1 + np.arctan2(By, np.cos(lat1) + Bx)
    #print "result: ",np.degrees(lat3),np.degrees(lon3)
    
    #put them in a form which the model can evaluate
    samples= np.array([list(a) for a in zip(lon3,lat3)])
    #print np.degrees(samples)
    
    #score the midpoint of the edge section and normalize it by the length
    distance = geocalc(np.degrees(lat1), np.degrees(lon1), np.degrees(lat2), np.degrees(lon2)) 
    density = model.score_samples(samples)*distance
    return density
   
def densitycalc2(lat0,lon0,lat1,lon1,distance,model,char_length=1e-2):
    phi1 = np.radians(lat0)
    lam1 = np.radians(lon0)
    phi2 = np.radians(lat1)
    lam2 = np.radians(lon1)

    delta = distance/EARTH_R   
    num_fracs = distance/char_length
   
    int_points = []
    for f in np.arange(0,1,1/num_fracs):
        a = np.sin((1-f)*delta)/np.sin(delta)
        b = np.sin(f*delta)/np.sin(delta)
        x = a*np.cos(phi1)*np.cos(lam1) + b*np.cos(phi2)*np.cos(lam2)
        y = a*np.cos(phi1)*np.sin(lam1) + b*np.cos(phi2)*np.sin(lam2)
        z = a*np.sin(phi1) + b*np.sin(phi2)
        new_phi = np.arctan2(z,np.sqrt(x**2 + y**2))
        new_lam = np.arctan2(y,x)
        int_points.append([new_lam,new_phi])
    int_points.append([lam1,phi1])
    int_array = np.asarray(int_points)
    density = sum(np.exp(model.score_samples(int_array)))
    return density

########################################
    
def get_closest_nodes(sg,pos0,pos1):
    nodes = np.array(sg.nodes())
    pos0_i = np.argmin(np.sum((nodes[:,::-1] - pos0)**2, axis=1))
    pos1_i = np.argmin(np.sum((nodes[:,::-1] - pos1)**2, axis=1))
    return pos0_i, pos1_i
 
def check_closest_node(sg,pos_input,closest_node):
    tolerance = 0.1
    nodes = sg.nodes()
    closest_lon,closest_lat = nodes[closest_node]
    distance = abs(geocalc(pos_input[0],pos_input[1],closest_lat,closest_lon))
    if distance > 0.1:
        return False
    else:
        return True
    
def get_shortest_path(sg,pos0_i,pos1_i):
    nodes = np.array(sg.nodes())
    path = nx.shortest_path(sg,
                        source=tuple(nodes[pos0_i]), 
                        target=tuple(nodes[pos1_i]),
                        weight='distance')
    return path
    
def get_photo_path(sg,pos0_i,pos1_i,alpha=1):
    get_photolength(sg,alpha)
    nodes = np.array(sg.nodes())
    path = nx.shortest_path(sg,
                        source=tuple(nodes[pos0_i]), 
                        target=tuple(nodes[pos1_i]),
                        weight='photolength')
    return path
    
def get_path_roads(sg,path):
    roads = pd.DataFrame([sg.edge[path[i]][path[i + 1]] 
                      for i in range(len(path) - 1)], 
                     columns=['FULLNAME', 'MTFCC', 
                              'RTTYP', 'distance'])
    return roads
    
def get_path_distance(roads):
    return roads['distance'].sum()
    
def get_full_path(path,sg):
    """Return the positions along a path."""
    p_list = []
    curp = None
    for i in range(len(path)-1):
        p = get_path(path[i], path[i+1],sg)
        if curp is None:
            curp = p
        #if np.sum((p[0]-curp)**2) > np.sum((p[-1]-curp)**2):
        if np.sum((p[0]-curp)**2) >= np.sum((p[-1]-curp)**2):
            p = p[::-1,:]
        p_list.append(p)
        curp = p[-1]
    return np.vstack(p_list) 

########################################  

def get_bounding_box_graph(sg):
    minlat=90
    maxlat=-90
    minlon=180
    maxlon=-180
    for node in sg.nodes():
        lon = node[0]
        lat = node[1]        
        if lon < minlon: minlon = lon
        if lon > maxlon: maxlon = lon
        if lat < minlat: minlat = lat
        if lat > maxlat: maxlat = lat        
    return (minlon,minlat),(maxlon,maxlat)

def reduce_graph(sg,city):
    walkable_types = (
        'primary',
        'secondary',
        'tertiary',
        'residential',
        'living_street',
        'pedestrian',
        'track',
        'steps',
        'path',
        'footway',
        'steps',
        'path'
    )
    remove = []
    for n0,n1 in sg.edges():
        lon1 = n0[0]
        lat1 = n0[1]
        lon2 = n1[0]
        lat2 = n1[1]
        if city.minx < lon1 < city.maxx and city.minx < lon2 < city.maxx and city.miny < lat1 < city.maxy and city.miny < lat2 < city.maxy:
            if sg.edge[n0][n1]['type'] in walkable_types:
                continue
            else:
                remove.append((n0,n1))
        else:
            remove.append((n0,n1))
               
    for nodes in remove:
        sg.remove_edge(nodes[0],nodes[1])
    
def reduce_graph_to_city(sg,city):
    remove = []
    for n0,n1 in sg.edges():
        lon1 = n0[0]
        lat1 = n0[1]
        lon2 = n1[0]
        lat2 = n1[1]
        if city.minx < lon1 < city.maxx and city.minx < lon2 < city.maxx and city.miny < lat1 < city.maxy and city.miny < lat2 < city.maxy:
            continue
        else:
            remove.append((n0,n1))   
    for nodes in remove:
        sg.remove_edge(nodes[0],nodes[1])
        
def remove_nonwalkable_paths(sg):
    walkable_types = (
        'primary',
        'secondary',
        'tertiary',
        'residential',
        'living_street',
        'pedestrian',
        'track',
        'steps',
        'path',
        'footway',
        'steps',
        'path'
    )
    remove = []
    for n0,n1 in sg.edges():
        if sg.edge[n0][n1]['type'] in walkable_types:
            continue
        else:
            remove.append((n0,n1))               
    for nodes in remove:
        sg.remove_edge(nodes[0],nodes[1])
            
def get_graph_info_for_web(sg,pos0,pos1,alpha=1):
    pos0_i,pos1_i = get_closest_nodes(sg,pos0,pos1)
    if check_closest_node(sg,pos0,pos0_i) and check_closest_node(sg,pos1,pos1_i):
        pass
    else: 
        return False
    
    spath = get_shortest_path(sg,pos0_i,pos1_i)
    sroads = get_path_roads(sg,spath)
    slinepath = get_full_path(spath,sg)
    sdistance = get_path_distance(sroads)
    
    ppath = get_photo_path(sg,pos0_i,pos1_i,alpha)
    proads = get_path_roads(sg,ppath)
    plinepath = get_full_path(ppath,sg)
    pdistance = get_path_distance(proads)
    
    return slinepath,sdistance,plinepath,pdistance


def get_points_along_path(path, num_points):
    points = []
    num = num_points + 2
    length = float(len(path))
    
    if num > len(path):
        num = len(path)
    
    for i in range(num):
        points.append(path[int(math.ceil(i * length / num))])
    return points[1:-1]
    
def get_type_set(sg):
    type_set = set()
    for n0,n1 in sg.edges_iter():
        type_set.add(sg_full[n0][n1]['type'])
    return type_set
    
def remove_extra_keys_from_edges(sg):
    keep = ['Json','distance','density']
    for n0,n1 in sg.edges_iter():
        remove = set(sg[n0][n1].keys()) - set(keep)
        for key in remove:
            del sg[n0][n1][key]    
        
    
        



