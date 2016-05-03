# Embedded file name: /home/vintello/PycharmProjects/webdav-ajax-library/Sources/Plugins/LinuxMounter/Source/document_opener.py
import sys
import operations
from urlparse import urlparse
from urlparse import urljoin, SplitResult
import re
import os.path
import urllib
from gui import *
import logging
from logging.handlers import SysLogHandler
type_logger = logging.DEBUG
logger = logging.getLogger('ithiteditdocumentopener')
logger.setLevel(type_logger)
syslog = SysLogHandler(address='/dev/log')
formatter = logging.Formatter('%(name)s %(levelname)s:%(filename)s:%(lineno)d -- %(message)s')
syslog.setFormatter(formatter)
logger.addHandler(syslog)
ch = logging.StreamHandler()
ch.setLevel(type_logger)
logger.addHandler(ch)

class Url_Parser(object):

    def __init__(self):
        self.default_port = {'http': 80,
         'https': 443}
        self.scheme = ''
        self.netloc = ''
        self.path = ''
        self.port = ''

    def url_parse(self, url):
        self.url = url
        pars_data = urlparse(url, 'http')
        self.scheme = pars_data.scheme
        self.netloc = pars_data.netloc
        self.path = self._cut_path()
        self._normalize_port(self.netloc)

    def set_scheme(self, scheme):
        self.scheme = scheme

    def set_netloc(self, netloc):
        self.netloc = netloc

    def set_path(self, path):
        self.path = path

    def set_port(self, port):
        self.port = port

    def get_url(self):
        if self.port and self.netloc:
            netloc = self.netloc + ':' + str(self.port)
        else:
            netloc = self._normalize_port(self.netloc)
        url = SplitResult(scheme=self.scheme, netloc=netloc, path=self.path, query='', fragment='').geturl()
        return url

    def _cut_path(self):
        scheme_netloc = SplitResult(scheme=self.scheme, netloc=self.netloc, path='', query='', fragment='').geturl()
        path = re.sub(scheme_netloc, '', self.url)
        return path

    def _normalize_port(self, netloc):
        splited_data = netloc.split(':')
        if len(splited_data) == 1:
            if self.scheme == '':
                self.scheme = 'http'
            self.port = self.default_port[self.scheme]
        elif len(splited_data) == 2:
            if not self.port:
                self.port = splited_data[1]
                self.netloc = splited_data[0]
        res = splited_data[0] + ':' + str(self.port)
        return res


class URL_EncoderNormalizer(object):

    def __init__(self):
        self.mountPath = ''
        self.filePath = ''

    def set_url(self, url):
        davPathArgument = url
        self.url = re.sub('^\\w+:', '', davPathArgument)
        mountPattern, filePattern = self._split_mountpath_filepath()
        self.normalize_path(mountPattern, filePattern)
        self.replace_plus()
        self.mountPath = urllib.unquote(self.mountPath)
        self.filePath = urllib.unquote(self.filePath)

    def replace_plus(self):
        self.mountPath = re.sub('\\+', '%20', self.mountPath)
        self.filePath = re.sub('\\+', '%20', self.filePath)

    def _split_mountpath_filepath(self):
        data = re.match('^(?P<mount>.+?)(\\||%7C)(?P<path>.+?)$', self.url)
        if data:
            mountPattern = data.group('mount')
            filePattern = data.group('path')
        elif re.match('^(\\||%7C)(?P<path>.+?)$', self.url):
            data = re.match('^(\\||%7C)(?P<path>.+?)$', self.url)
            url_path_file = Url_Parser()
            url_path_file.url_parse(data.group('path'))
            url_path_file.get_url()
            if url_path_file.path[-1] == '/':
                path = url_path_file.path
            else:
                path_list = url_path_file.path.split('/')
                path = '/'.join(path_list[:len(path_list) - 1]) + '/'
            mountPattern = SplitResult(scheme=url_path_file.scheme, netloc=url_path_file.netloc, path=path, query='', fragment='').geturl()
            filePattern = data.group('path')
        elif re.match('^(?P<path>.+?)$', self.url):
            data = re.match('^(?P<path>.+?)$', self.url)
            url_path_file = Url_Parser()
            url_path_file.url_parse(data.group('path'))
            url_path_file.get_url()
            if url_path_file.path[-1] == '/':
                path = url_path_file.path
            else:
                path_list = url_path_file.path.split('/')
                path = '/'.join(path_list[:len(path_list) - 1]) + '/'
            mountPattern = SplitResult(scheme=url_path_file.scheme, netloc=url_path_file.netloc, path=path, query='', fragment='').geturl()
            filePattern = data.group('path')
        else:
            raise Exception('Wrong number of parameters.\nProgram requires two parameters: "mount path" and "file path".')
        logger.info('mountPattern: %s filePattern: %s' % (mountPattern, filePattern))
        return (mountPattern, filePattern)

    def _parse_url(self):
        url_parser = Url_Parser()
        url_parser.url_parse(self.url)
        self.scheme = url_parser.scheme
        self.netloc = url_parser.netloc
        self.path = ''

    def normalize_path(self, mountPattern, filePattern):
        filePatternObj = Url_Parser()
        filePatternObj.url_parse(filePattern)
        filePatternObj.get_url()
        MountPatternObj = Url_Parser()
        MountPatternObj.url_parse(mountPattern)
        MountPatternObj.get_url()
        if filePatternObj.scheme and filePatternObj.netloc:
            davRootPath = filePatternObj.scheme + '://' + filePatternObj.netloc + ':' + str(filePatternObj.port)
        else:
            davRootPath = MountPatternObj.scheme + '://' + MountPatternObj.netloc + ':' + str(filePatternObj.port)
        if mountPattern == '':
            head, tail = os.path.split(filePattern)
            if tail == '':
                mountPath = filePattern
            else:
                mountPath = os.path.dirname(filePattern)
        else:
            davRelPath = MountPatternObj.path
            mountPath = urljoin(davRootPath, davRelPath) if urljoin(davRootPath, davRelPath)[-1] == '/' else urljoin(davRootPath, davRelPath) + '/'
        filePath = filePatternObj.get_url()
        self.mountPath = mountPath
        self.filePath = filePath


class DirectRunError(Exception):
    pass


def error_message_show(title, message):
    error_message = MessageDialogWindow()
    error_message.show_error(message, title)


if __name__ == '__main__':
    try:
        if len(sys.argv) < 2:
            msg = 'This is a protocol application. It is executed when a file from a web page is being open using davX: protocol.\n'
            msg += 'Do not run this application directly.'
            raise DirectRunError(msg)
        url_parser = URL_EncoderNormalizer()
        url_parser.set_url(sys.argv[1])
        mountPath = url_parser.mountPath
        filePath = url_parser.filePath
        logger.debug('mountPath: ' + mountPath)
        logger.debug('filePath: ' + filePath)
        operations.open_document(mountPath, filePath)
        logger.info('Mounting success')
    except DirectRunError as e:
        logger.error(e)
        error_message_show('Application Launch Error - IT Hit Edit Document Opener', e.message)
        sys.exit(2)
    except Exception as e:
        logger.error(e)
        error_message_show('Error - IT Hit Edit Document Opener', e.message)
        sys.exit(1)