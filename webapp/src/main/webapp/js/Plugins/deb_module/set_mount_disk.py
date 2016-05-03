# Embedded file name: /home/vintello/PycharmProjects/webdav-ajax-library/Sources/Plugins/LinuxMounter/Source/set_mount_disk.py
import subprocess
import logging
from logging.handlers import SysLogHandler
import io, sys
import os, pwd, grp
import urllib
import json
type_logger = logging.WARNING
logger = logging.getLogger('ithiteditdocumentopener.set_mount_disk')
logger.setLevel(type_logger)
syslog = SysLogHandler(address='/dev/log')
formatter = logging.Formatter('%(name)s %(levelname)s:%(filename)s:%(lineno)d -- %(message)s')
syslog.setFormatter(formatter)
logger.addHandler(syslog)
ch = logging.StreamHandler()
ch.setLevel(type_logger)
logger.addHandler(ch)

class Fstab(io.FileIO):

    class Entry(object):

        def __init__(self, device, mountpoint, filesystem, options, d = 0, p = 0):
            self.device = device
            self.mountpoint = mountpoint
            self.filesystem = filesystem
            if not options:
                options = 'defaults'
            self.options = options
            self.d = int(d)
            self.p = int(p)

        def __eq__(self, o):
            return str(self) == str(o)

        def __str__(self):
            return '{} {} {} {} {} {}'.format(self.device, self.mountpoint, self.filesystem, self.options, self.d, self.p)

    DEFAULT_PATH = os.path.join(os.path.sep, 'etc', 'fstab')

    def __init__(self, path = None):
        if path:
            self._path = path
        else:
            self._path = self.DEFAULT_PATH
        super(Fstab, self).__init__(self._path, 'rb+')

    def _hydrate_entry(self, line):
        return Fstab.Entry(*filter(lambda x: x not in ('', None), line.strip('\n').split()))

    @property
    def entries(self):
        self.seek(0)
        for line in self.readlines():
            line = line.decode('us-ascii')
            try:
                if line.strip() and not line.strip().startswith('#'):
                    yield self._hydrate_entry(line)
            except ValueError:
                pass

    def get_entry_by_attr(self, attr, value):
        for entry in self.entries:
            e_attr = getattr(entry, attr)
            if e_attr == value:
                return entry

        return None

    def add_entry(self, entry):
        if self.get_entry_by_attr('device', entry.device):
            return False
        self.write((str(entry) + '\n').encode('us-ascii'))
        self.truncate()
        return entry

    def remove_entry(self, entry):
        self.seek(0)
        lines = [ l.decode('us-ascii') for l in self.readlines() ]
        found = False
        for index, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#'):
                if self._hydrate_entry(line) == entry:
                    found = True
                    break

        if not found:
            return False
        lines.remove(line)
        self.seek(0)
        self.write(''.join(lines).encode('us-ascii'))
        self.truncate()
        return True

    @classmethod
    def remove_by_mountpoint(cls, mountpoint, path = None):
        fstab = cls(path=path)
        entry = fstab.get_entry_by_attr('mountpoint', mountpoint)
        if entry:
            return fstab.remove_entry(entry)
        return False

    @classmethod
    def add(cls, device, mountpoint, filesystem, options = None, path = None):
        return cls(path=path).add_entry(Fstab.Entry(device, mountpoint, filesystem, options=options))


class Mounter_fast(object):

    def __init__(self, file_temp):
        self.davfs_folder_name = '.davfs2'
        self.davfs_secret_file_name = 'secrets'
        self.file_temp = file_temp
        self.read_data()
        self.validate_user_in_group_davfs2()
        self.set_permissions_for_mount_davfs()
        self.find_or_create_in_fstab()
        self.davfs_secret_file()

    def read_data(self):
        temp_file = open(temp_file_name, 'r')
        data_file = temp_file.read()
        data = json.loads(data_file)
        self.user = data['user_login']
        self.mountPath = data['mountPath']
        self.dirPath = data['dirPath']
        self.home_folder = data['home_folder']
        self.mount_user_login = data['mount_user_login']
        self.mount_user_pass = data['mount_user_pass']

    def set_permissions_for_mount_davfs(self):
        file_name = os.path.join('/', 'usr', 'sbin', 'mount.davfs')
        os.system('chmod 4755 %s' % file_name)

    def davfs_secret_file(self):
        logger.info('start create davfs2 secret file')
        dirPath = os.path.join(self.home_folder, self.davfs_folder_name)
        uid_user = pwd.getpwnam(self.user).pw_uid
        gid_user = grp.getgrnam(self.user).gr_gid
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
            os.system('chown %s:%s %s' % (self.user, self.user, dirPath))
            logger.debug('folder %s is create' % dirPath)
        else:
            logger.debug('folder %s was found' % dirPath)
        file_name = os.path.join(dirPath, self.davfs_secret_file_name)
        print file_name
        logger.debug('create file - %s ' % file_name)
        with open(file_name, 'w+') as secret_file:
            logger.debug(self.mountPath + ' ' + self.mount_user_login + ' "' + self.mount_user_pass + '"')
            secret_file.writelines(self.mountPath + ' ' + self.mount_user_login + ' "' + self.mount_user_pass + '"')
        os.chmod(file_name, 384)
        os.chown(file_name, uid_user, gid_user)

    def validate_user_in_group_davfs2(self, group_name = 'davfs2'):
        logger.debug('Validation is user in group')
        groups = [ g.gr_name for g in grp.getgrall() if self.user in g.gr_mem ]
        gid = pwd.getpwnam(self.user).pw_gid
        groups.append(grp.getgrgid(gid).gr_name)
        if group_name in groups:
            logger.info('User %s is in group %s' % (self.user, group_name))
        else:
            logger.warning('User %s not in group %s' % (self.user, group_name))
            command = 'usermod -a -G %s %s' % (group_name, self.user)
            logger.debug('command for add user %s' % command)
            os.system(command)
            logger.debug('added sucessfull')

    def find_or_create_in_fstab(self):
        logger.debug('Validation file /etc/fstab on is have mountin resource ')
        fstab = Fstab()
        fstab.add(self.mountPath, self.dirPath, filesystem='davfs', options='user,rw,noauto')


if __name__ == '__main__':
    try:
        temp_file_name = urllib.unquote(sys.argv[1])
        if temp_file_name:
            mounter = Mounter_fast(temp_file_name)
        else:
            raise 'execute this file require temp file with params mounting'
    except Exception as e:
        logger.error('Error:' + e)
        raise