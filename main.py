import json
import os
import sys

import configparser
import logging
import urllib.parse
from pathlib import Path
import download

import pyfomod
import pynxm
import plac
import xdg
from logging import warning, error

assert sys.version_info >= (3, 0)
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

api_key = os.environ['NEXUS_API_KEY']
print(api_key)
nexus = pynxm.Nexus(api_key)


def extract_parts_from_url(url: str):
    # nxm://fallout4/mods/4598/files/209596?key=7dI_GAPTr7KUGuxe2kWGww&expires=1629807989&user_id=5177197
    # ParseResult(scheme='nxm', netloc='fallout4', path='/mods/4598/files/209596', params='', query='key=7dI_GAPTr7KUGuxe2kWGww&expires=1629807989&user_id=5177197', fragment='')
    urlparts = urllib.parse.urlparse(url)
    fileinfo = urlparts.path.split('/')
    qi = urllib.parse.parse_qs(urlparts.query)
    return {'scheme': urlparts.scheme, 'game': urlparts.netloc, 'mod_id': fileinfo[2], 'file_id': fileinfo[4],
            'key': qi['key'], 'expires': qi['expires']}


# Why do I have to urlencode this manually, wtf nexus.
# Going to assume you won't fuck up in your query parameters at least. *knocks on wood*
def urlencode_url(url):
    p = urllib.parse.urlparse(url)
    return "{0}://{1}/{2}?{3}".format(p.scheme, p.netloc, urllib.parse.quote(p.path), p.query)


def download_action(url, downloadfolder):
    parts = extract_parts_from_url(url)
    if parts['scheme'] != "nxm":
        logging.fatal("Invalid url scheme (needs to be nxm).")
        quit(-1)
    mod_file_details = nexus.mod_file_details(parts['game'], parts['mod_id'], parts['file_id'])
    print(mod_file_details)
    downloadinfo = nexus.mod_file_download_link(parts['game'], parts['mod_id'], parts['file_id'], parts['key'],
                                                parts['expires'])
    downloadloc = Path.joinpath(downloadfolder, mod_file_details['file_name']).__str__()

    url = urlencode_url(downloadinfo[0]['URI'])

    download.download(url, Path.joinpath(downloadfolder, downloadloc).__str__())
    #json.dump(downloadinfo)


@plac.opt("config", "Location of configuration file", type=Path)
def main(action, *args, config=xdg.xdg_config_home().joinpath(Path('./almm/almm.ini'))):
    """Alice's Linux Mod Manager"""
    cfg = config_setup(config)

    stagingfolder = Path(cfg['Main']['stagingfolder'])
    gamefolder = Path(cfg['Main']['gamefolder'])
    downloadfolder = Path(cfg['Main']['downloadfolder'])

    if not gamefolder.exists():
        logging.fatal("Gamefolder doesn't exist")
        quit(-1)

    if not stagingfolder.exists():
        logging.warning("Creating stagingfolder")
        stagingfolder.mkdir(511, True, False)

    if not downloadfolder.exists():
        logging.warning("Creating downloadfolder")
        downloadfolder.mkdir(511, True, False)

    # I want to use a match here but that doesn't release until 3.10
    if action == "download":
        url = args[0]
        download_action(url, downloadfolder)
    else:
        error("Invalid action " + action)
        quit(-1)

    # TODO Write code


# Takes care of making sure the config file exists and creates it if not
def config_setup(config):
    cfg = configparser.ConfigParser()
    if config.exists() and config.is_file():
        cfg.read(config)
        del config
    else:
        if config != xdg.xdg_config_home().joinpath(Path('./almm/almm.ini')):
            error("-config " + config.__str__() + ": File doesn't exists (or is not a valid configuration file).")
            quit(-1)
        warning("Configuration file doesn't exist, creating at " + config.__str__())
        if not config.parent.exists():
            config.parent.mkdir(511, True, False)

        config.write_text("[Version]\nrev=0\n[Main]\ngamefolder={0}\nstagingfolder={1}\ndownloadfolder={2}\n".format(
            Path.joinpath(xdg.xdg_data_home(), Path("./Steam/steamapps/common/Fallout 4/")).__str__(),
            Path.joinpath(xdg.xdg_data_home(), Path("./almm/staging/Fallout 4/")).__str__(),
            Path.joinpath(xdg.xdg_data_home(), Path("./almm/downloads/Fallout 4/")).__str__())
        )
        logging.fatal(
            "Created configuration file, please edit it at {0} and run the script again.".format(config.__str__()))
        quit()
    return cfg


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    plac.call(main)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
