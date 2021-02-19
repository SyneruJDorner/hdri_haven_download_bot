import sys, os, time, shutil, subprocess, json
import selenium_helper as selenium
from pyunpack import Archive
import requests
from progress.bar import Bar
from PIL import Image
from configparser import ConfigParser
import icon_lib


def get_json_data():
    with open('config.json') as json_file:
        data = json.load(json_file)
    return data


def download_wait(directory, timeout=1440, nfiles=None):
    seconds = 0
    dl_wait = True

    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)

        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        if (dl_wait == False):
            break
        seconds += 1
    return seconds


def getFolderSize(p):
   from functools import partial
   prepend = partial(os.path.join, p)
   return sum([(os.path.getsize(f) if os.path.isfile(f) else getFolderSize(f)) for f in map(prepend, os.listdir(p))])


def get_folder_path(child_name):
    save_path = get_json_data()['hdri_save_path']
    folder_path = []

    folder_path = [save_path + child_name + "\\1k",
            save_path + child_name + "\\2k",
            save_path + child_name + "\\4k",
            save_path + child_name + "\\8k"]

    return folder_path


def create_paths(child_name):
    paths = get_folder_path(child_name=child_name)

    try:
        for path in paths:
            os.makedirs(path)
    except OSError:
        pass
    else:
        pass
    return paths


def get_download_links(child_name):
    download_links = []

    download_links = ["https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.exr".format("1k", child_name, "1k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.exr".format("2k", child_name, "2k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.exr".format("4k", child_name, "4k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.exr".format("8k", child_name, "8k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.hdr".format("1k", child_name, "1k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.hdr".format("2k", child_name, "2k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.hdr".format("4k", child_name, "4k"),
                    "https://download.polyhaven.com/HDRIs/{0}/{1}_{2}.hdr".format("8k", child_name, "8k")]

    return download_links


def get_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')


def download_files(driver, child_name, path, debug=False):
    if (debug == True):
        print(child_name, path)

    download_links = get_download_links(child_name)
    download_path = get_download_path()

    for i, path in enumerate(path, start=0):
        if (getFolderSize(path) > 0):
            continue
        
        for _ in range(2):
            driver.get(download_links[i])
            download_wait(download_path)
            file_name = download_links[i].replace("https://download.polyhaven.com/HDRIs/", "")
            file_name = file_name[file_name.rindex('/')+1:]
            if (os.path.isfile(download_path + "\\" + file_name)):
                shutil.move(download_path + "\\" + file_name, path + "\\" + file_name)
                break
            else:
                i = i + 4
    return


def download_icon_file(driver, icon_src, child_name):
    save_path = get_json_data()['hdri_save_path']

    jpg_path = save_path + child_name + "\\" + 'Title.jpg'
    ico_path = save_path + child_name + "\\" + 'Title.ico'

    if (os.path.isfile(ico_path) == False):
        img = requests.get("https://hdrihaven.com" +  icon_src)
        with open(jpg_path, 'wb') as writer:
            writer.write(img.content)

        MAX_SIZE = (256, 256)
        
        image = Image.open(jpg_path)
        resize_img = image.resize(MAX_SIZE)
        resize_img.save(jpg_path)

        image = Image.open(jpg_path)
        image.thumbnail(MAX_SIZE)
        image.save(ico_path)
        os.remove(jpg_path)
        subprocess.check_call(["attrib","+H", ico_path])

        icon_lib.SetFolderIcon(save_path + child_name, ico_path, True)


def main(argv):
    driver, wait = selenium.init(get_json_data()['driver_path'])
    driver.get("https://hdrihaven.com/hdris/?o=date_published")

    grid_items_xpath = '/html/body/div/div[3]/div[3]/div[2]'
    grid_items_element = wait.until(selenium.EC.presence_of_element_located((selenium.By.XPATH, grid_items_xpath)))
    child_elements = grid_items_element.find_elements(selenium.By.XPATH, ".//a")
    bar = Bar('Downloading', fill='█', suffix='%(percent)d%%', max=len(child_elements))
    child_names = []

    for child in child_elements:
        name = child.find_element(selenium.By.XPATH, ".//div/div[2]/div/div/h3").get_attribute('innerText').lower().replace(" ", "_")
        icon_src = child.find_element(selenium.By.XPATH, ".//div/div[1]/img[2]").get_attribute("data-src")
        data = { "name": name, "img_src": icon_src }
        child_names.append(data)
        
    for child in child_names:
        bar.next()
        path = create_paths(child["name"])

        download_files(driver=driver, child_name=child["name"], path=path, debug=False)
        download_icon_file(driver, child["img_src"], child["name"])

    bar.finish()
    print("Completed! Shutting down")
    driver.close()
    driver.quit()
    return


if __name__ == "__main__":
    main(sys.argv)