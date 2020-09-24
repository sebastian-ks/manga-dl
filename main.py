import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from datetime import date
import os
import requests
from _ePubMaker import EPubMaker
import shutil
from PIL import Image
import time
from optparse import OptionParser

UPDATE_MSG = "You are using an outdated version of manga-dl\n\nMake sure you are using the latest version"
WEBSITE_MSG = "This site is not supported by manga-dl!\n\nCheck README 2.txt to see which sites are supported"

def main(argv):

    parser = OptionParser()
    parser.add_option("-t","--title",dest="title",help='choose custom title for eBook')
    (options, args) = parser.parse_args()

    title = options.title
    if not len(argv) > 1:
        url = input("url: ")
        title = input("title (type 'na' to auto-generate title): ")

    else:
        url = argv[1]

    if not "mangazuki" in url and not "bato.to" in url:
        print(WEBSITE_MSG)
        return

    print("Connecting...")

    #start driver
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome("dependencies\\chromedriver.exe",options=options)
    driver.set_window_position(-10000,0)

    try:
        driver.get(url)
    except:
        print("Requested url does not exist")
        return
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass

    #actual crawling process
    try:
        #mangazuki
        if "mangazuki" in url:
            if title is None or title == "na":
                breadcrumb = driver.find_element_by_xpath("//ol[@class='breadcrumb']")
                title = breadcrumb.find_element_by_xpath(".//li[@class='active']").text
            divs = driver.find_elements_by_xpath("//div[@class='page-break']")

        #bato
        if "bato.to" in url:
            if title is None or title == "na":
                series = driver.find_element_by_xpath("//h3[@class='nav-title']").text
                optgroup = driver.find_element_by_xpath("//optgroup[@label='Chapters']")
                chapter = optgroup.find_element_by_xpath("//option[@selected='selected']").text.split("\n")[0]
                title = series+" "+chapter
            divs = driver.find_elements_by_xpath("//div[@class='item invisible']")

    except:
        print(UPDATE_MSG)
        return


    #manage directories

    #cleanup if could not delete on last run
    constant_dirs = ["dependencies","downloads","__pycache__","assets"]
    dirs = (d for d in os.listdir(".") if os.path.isdir(d))
    for di in dirs:
        if di not in constant_dirs:
            shutil.rmtree(di)

    #create temporary directory
    t = datetime.now().strftime("%H;%M")
    dir = date.today().strftime("%d-%m-%Y")+";"+t
    if not os.path.exists("downloads"):
        os.mkdir("downloads")
    os.mkdir(dir)
    os.mkdir(dir+"\\last_chapter_backup")

    i = 0
    tag = ""


    print("Downloading...")

    for div in divs:
        #naming conventions
        i = i+1
        if i >= 100:
            tag = str(i)
        elif i >= 10:
            tag = "0"+str(i)
        else:
            tag = "00"+str(i)

        #write data to temporary directory
        src = div.find_element_by_xpath(".//img").get_attribute('src')
        file = dir+"\\last_chapter_backup\\"+tag+".jpg"

        if not os.path.exists(file):
            r = requests.get(src)
            with open(file, 'wb') as outfile:
                outfile.write(r.content)

        #rotating operation for 2 page panels
        out = Image.open(file)
        w, h = out.size
        if w > h:
            try:
                out.transpose(Image.ROTATE_270).save(file)
            except OSError:
                os.remove(file)


    print("Converting...")
    output_file = "downloads\\"+title+'.epub'
    creator = EPubMaker(None,dir,output_file,title)
    creator.run()

    driver.quit()
    print("Done")


if __name__ == '__main__':
    main(sys.argv)
