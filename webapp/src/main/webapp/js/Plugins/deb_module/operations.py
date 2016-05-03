# Embedded file name: /home/vintello/PycharmProjects/webdav-ajax-library/Sources/Plugins/LinuxMounter/Source/operations.py
import sys
import subprocess
import os
import re
from gui import *
import urllib
import grp, pwd
import tempfile
import json
from urlparse import urlsplit, SplitResult
import logging
logger = logging.getLogger('ithiteditdocumentopener')

def open_folder(mountPath, folderPath):
    open_webdav_path(mountPath, folderPath)


def open_document(mountPath, filePath):
    open_webdav_path(mountPath, filePath)


def open_webdav_path(mountPath, docPath):
    serverUri = mountPath
    filePath = docPath
    if docPath.startswith(mountPath):
        filePath = docPath.replace(mountPath, '')
    if is_dolphin_installed():
        open_via_kde(serverUri, filePath)
    else:
        open_via_davfs(mountPath, serverUri, filePath)


def get_server_uri(sourceUri):
    return sourceUri.replace('https://', '').replace('http://', '')


def is_dolphin_installed():
    if subprocess.call('dolphin --help', shell=True) == 0:
        return True
    return False


def open_via_kde(serverUri, filePath):
    logger.info('Open in KDE')
    logger.info('serverUri: %s filePath: %s' % (serverUri, filePath))
    data = urlsplit(serverUri)
    logger.info('**'.join(data))
    if data.scheme == 'https':
        scheme_netloc = SplitResult(scheme='webdavs', netloc=data.netloc, path=data.path + filePath, query='', fragment='').geturl()
    else:
        scheme_netloc = SplitResult(scheme='webdav', netloc=data.netloc, path=data.path + filePath, query='', fragment='').geturl()
    logger.info("xdg-open '%s'" % scheme_netloc)
    proc_runner = subprocess.call("xdg-open '%s'" % scheme_netloc, shell=True)
    if proc_runner == 0:
        return True
    return False


def open_via_davfs(mountPath, serverUri, filePath):
    logger.info('Open in davfs2')
    if not is_davfs_installed():
        raise NotImplementedError('Unable to mount WebDAV file system because davfs is not installed.', 'File System Mounting Error')
    logger.info('Davfs is available')
    mountFolderPath = ''
    mount_flg, login, password = is_location_mounted(mountPath, serverUri)
    if mount_flg:
        logger.debug('Mount location already exists')
        mountFolderPath = get_local_mount_folder(mountPath)
        logger.debug('Mount folder path: ' + mountFolderPath)
    else:
        create_dir_if_not_exists(get_local_mount_folder(mountPath))
        logger.debug('Mounting location')
        mountFolderPath = mount_davfs_old(mountPath, serverUri, login, password)
    logger.debug('Open file command:')
    urlToOpen = 'xdg-open "' + mountFolderPath + '/' + filePath + '"'
    logger.debug(urlToOpen)
    openResult = os.system(urlToOpen)
    if openResult != 0:
        logger.debug('Opening document failed. Error code: ' + str(openResult))
        raise IOError('Opening document failed. Error code: ' + str(openResult))


def is_davfs_installed(name_pkg = 'davfs2'):
    status = False
    p1 = subprocess.Popen(['dpkg', '--get-selections', name_pkg], stdout=subprocess.PIPE)
    out, err = p1.communicate()
    if out:
        result = re.findall(name_pkg + '.+?(\\w+)$', out)
        if result:
            if result[0] == u'install':
                status = True
    return status


def is_location_mounted(mountPath, serverUri):
    mount_flg = login = password = False
    directory = get_local_mount_folder(mountPath)
    mount_flg = os.path.exists(directory) and len(os.listdir(directory)) > 0
    if not mount_flg:
        file_secrets = file_name = os.path.join(os.environ['HOME'], '.davfs2', 'secrets')
        if os.path.exists(file_secrets):
            login_window = LoginWindow()
            login, password = login_window.get_user_pw('Please specify your ' + serverUri + ' credentials', serverUri + ' Credentials')
            str_wal = ' '.join([mountPath, login, '"' + password + '"'])
            with open(file_secrets, 'r+') as data_file:
                data_file.write(str_wal)
            cmd = 'mount %s' % mountPath
            logger.debug('Mount davfs test with command: %s' % cmd)
            result = subprocess.call(cmd, shell=True)
            if result == 0:
                mount_flg = True
    return (mount_flg, login, password)


def get_local_mount_folder(mountPath):
    folderName = 'webdav' + mountPath.replace('\\', '_').replace('/', '_')
    directory = '.tmp/webdav/'
    user_home_folder = os.environ['HOME']
    folder_home_Name = os.path.join(user_home_folder, directory, folderName)
    mount_to = os.path.abspath(folder_home_Name)
    return mount_to


def create_dir_if_not_exists(dirPath):
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)


def mount_davfs(mountPath, serverUri, login = None, password = None):
    dirPath = get_local_mount_folder(mountPath)
    create_dir_if_not_exists(dirPath)
    if not login:
        login_window = LoginWindow()
        login, password = login_window.get_user_pw('Please specify your ' + serverUri + ' credentials', serverUri + ' Credentials')
        logger.debug('Trying to mount: ' + os.path.abspath(dirPath))
    user_login = pwd.getpwuid(os.getuid())[0]
    home_folder = os.environ['HOME']
    path_to_lib = os.path.dirname(os.path.realpath(__file__))
    temp_file = tempfile.NamedTemporaryFile(bufsize=0)
    data_for_send = {'user_login': user_login,
     'mountPath': mountPath,
     'dirPath': dirPath,
     'home_folder': home_folder,
     'mount_user_login': login,
     'mount_user_pass': password}
    try:
        json.dump(data_for_send, temp_file)
        if not os.path.exists(os.path.join(path_to_lib, 'set_mount_disk.pyo')):
            mount_py_file_ext = 'py'
            key = ''
        else:
            mount_py_file_ext = 'pyo'
            key = '-O '
        mounter_cmd = 'set_mount_disk.%s %s' % (mount_py_file_ext, temp_file.name)
        command = ['gksudo', 'python %s%s/%s' % (key, path_to_lib, mounter_cmd)]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out, err = p.communicate()
        logger.info('out: %s' % out)
        logger.info('err: %s' % err)
    except:
        raise
    finally:
        temp_file.close()

    cmd = 'mount %s' % dirPath
    logger.debug('Mount davfs command:')
    logger.debug(cmd)
    result = 0
    result = subprocess.call(cmd, shell=True)
    if result != 0:
        logger.error('Mounting failed. Error code: ' + str(result))
        raise IOError('Mounting failed. Error code: ' + str(result))
    logger.info('Mounting success')
    mount_to = os.path.abspath(dirPath)
    logger.debug('mount_to: ' + mount_to)
    return mount_to


def mount_davfs_old(mountPath, serverUri, login, password):

    def cut_message_title_long(title):
        long_title_limit = 30
        if len(title) > long_title_limit:
            splitet_title = title.split('/')
            title_temp = ''
            for block in splitet_title:
                title_temp += block + '/'
                if len(title_temp) > long_title_limit:
                    title_temp += '...'
                    break

            title = title_temp
        return title

    dirPath = get_local_mount_folder(mountPath)
    create_dir_if_not_exists(dirPath)
    login_window = LoginWindow()
    login, password = login_window.get_user_pw('Please specify your ' + cut_message_title_long(serverUri) + ' credentials', cut_message_title_long(serverUri) + ' Credentials')
    logger.debug('Trying to mount: ' + os.path.abspath(dirPath))
    cmd = 'gksudo "bash -c \'echo {1} | mount -t davfs -o uid=$USER,username={0} \\\'{2}\\\' \\\'{3}\\\' \'"'.format(login, password, urllib.unquote(serverUri), os.path.abspath(dirPath))
    logger.debug('Mount davfs command:')
    logger.debug(cmd)
    result = subprocess.call(cmd, shell=True)
    if result != 0:
        logger.error('Mounting failed. Error code: ' + str(result))
        raise IOError('Mounting failed. Error code: ' + str(result))
    logger.info('Mounting success')
    mount_to = os.path.abspath(dirPath)
    return mount_to