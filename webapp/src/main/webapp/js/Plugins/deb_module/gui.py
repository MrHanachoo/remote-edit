# Embedded file name: /home/vintello/PycharmProjects/webdav-ajax-library/Sources/Plugins/LinuxMounter/Source/gui.py
from gi.repository import Gtk
import logging
logger = logging.getLogger('ithiteditdocumentopener')

class LoginWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)
        self.long_title_limit = 30

    def get_user_pw(self, message, title = ''):
        dialogWindow = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, message)
        dialogWindow.set_title(title)
        dialogWindow.set_default_response(Gtk.ResponseType.OK)
        dialogBox = dialogWindow.get_content_area()
        topBox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        dialogBox.pack_start(topBox, False, False, 0)
        loginBox = Gtk.Box(spacing=36)
        loginLabel = Gtk.Label()
        loginLabel.set_text('Login:')
        loginEntry = Gtk.Entry()
        loginEntry.set_size_request(250, 0)
        loginBox.pack_start(loginLabel, True, True, 0)
        loginBox.pack_start(loginEntry, True, True, 0)
        topBox.pack_start(loginBox, True, True, 0)
        pwdBox = Gtk.Box(spacing=6)
        pwdLabel = Gtk.Label()
        pwdLabel.set_text('Password:')
        pwdEntry = Gtk.Entry()
        pwdEntry.set_visibility(False)
        pwdEntry.set_size_request(250, 0)
        pwdBox.pack_start(pwdLabel, True, True, 0)
        pwdBox.pack_start(pwdEntry, True, True, 0)
        topBox.pack_start(pwdBox, True, True, 0)
        pwdEntry.connect('activate', self.on_enter, dialogWindow)
        dialogWindow.show_all()
        response = dialogWindow.run()
        login = loginEntry.get_text() or 'nologin'
        pwd = pwdEntry.get_text() or 'nopass'
        dialogWindow.destroy()
        if response == Gtk.ResponseType.OK:
            return (login, pwd)
        else:
            return ('nologin', 'nopass')

    def on_enter(self, window, *args):
        args[0].response(Gtk.ResponseType.OK)


class MessageDialogWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)

    def show_error(self, message, title = ''):
        window = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, message)
        window.set_title(title)
        window.set_default_response(Gtk.ResponseType.OK)
        window.run()