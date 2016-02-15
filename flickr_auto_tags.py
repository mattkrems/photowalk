from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
import time
import random
import pymysql as mdb
import pandas as pd
import utils

def get_auto_tags(driver,user_id,photo_id):
    link = 'https://www.flickr.com/photos/' + str(user_id) + '/' + str(photo_id) + '/'
    #driver = webdriver.Firefox() # webdriver.PhantomJS()
    print link
    
    driver.get(link)
    time.sleep(random.uniform(0,2))
    try:
        WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, "autotag")))
        html_page = driver.page_source    
        soup = BeautifulSoup(html_page)
        views = soup.find('span',{'class':"view-count-label"}).text.replace('\n','').replace('\t','')
        faves = soup.find('span',{'class':"fave-count-label"}).text.replace('\n','').replace('\t','')
        comments = soup.find('span',{'class':"comment-count-label"}).text.replace('\n','').replace('\t','')
        text=[x.text.strip('\n') for x in soup.find_all('li', {'class':"autotag"})]
        auto_tags = ','.join([x.replace(' ','+') for x in text])       
    except TimeoutException:
        html_page = driver.page_source
        soup = BeautifulSoup(html_page)
        try:
            views = soup.find('span',{'class':"view-count-label"}).text.replace('\n','').replace('\t','')
            faves = soup.find('span',{'class':"fave-count-label"}).text.replace('\n','').replace('\t','')
            comments = soup.find('span',{'class':"comment-count-label"}).text.replace('\n','').replace('\t','')
            auto_tags = ''
        except AttributeError:
            return '-1',None,None,''

    return views,faves,comments,auto_tags
    
if __name__ == '__main__':
    config = utils.get_config('config.ini')
    
    host = config['db']['host']
    user = config['db']['user']
    password = config['db']['password']
    db_name = config['db']['db']
    table_name = config['db']['table']


    con = mdb.connect(host=host,user=user,password=password,db=db_name,charset='utf8mb4')
    cur = con.cursor() 
    query = '''SELECT id,user_id from photos where location='sf' and date_taken between '2012-07-01' and NOW() and auto_tags is NULL;'''
    df = pd.read_sql(query,con)
    print len(df)

    driver = webdriver.Firefox()
    #driver = webdriver.PhantomJS()
    driver.set_window_size(640, 480)
    
    for photo_id,user_id in zip(df.id,df.user_id):
        views,faves,comments,auto_tags = get_auto_tags(driver,user_id,photo_id)
        
        
        cur.execute('''UPDATE photos SET views=%s WHERE id=%s''',(int(views.replace(',','')),str(photo_id)))
        cur.execute('''UPDATE photos SET auto_tags=%s WHERE id=%s''',(auto_tags.encode('utf-8'),str(photo_id)))
        if views != '-1':            
            print photo_id,user_id,views,faves,comments,auto_tags
            cur.execute('''UPDATE photos SET num_favs=%s WHERE id=%s''',(int(faves.replace(',','')),str(photo_id)))
            cur.execute('''UPDATE photos SET num_comments=%s WHERE id=%s''',(int(comments.replace(',','')),str(photo_id)))
        con.commit()
              
    driver.quit()
