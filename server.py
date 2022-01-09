import argparse
import configparser
import dis
import logging
import os
import sys
import threading
from json import JSONDecodeError
from time import time, sleep

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog

import logger.server_log_config
from logger.func_logger import Log
from select import select
import socket

from common.utils import get_message, send_message, port, server_ip
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE_TEXT, MESSAGE, SENDER, RESPONSE_200, RESPONSE_400, DESTINATION, \
    EXIT, GET_CONTACTS, USER_LOGIN, RESPONSE_202, ALERT, ADD_CONTACT, DEL_CONTACT, USER_ID
from models.server_db import ServerDB

_logger = logging.getLogger('server')
active_clients_changed = True
conflag_lock = threading.Lock()


def gui_create_model(database):
    list_users = database.active_clients_list()
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
    for row in list_users:
        _user, _port, _ip, _time = row
        _user = QStandardItem(_user)
        _user.setEditable(False)
        _ip = QStandardItem(_ip)
        _ip.setEditable(False)
        _port = QStandardItem(str(_port))
        _port.setEditable(False)
        _time = QStandardItem(str(_time.replace(microsecond=0)))
        _time.setEditable(False)
        list_table.appendRow([_user, _ip, _port, _time])
    return list_table


def create_stat_model(database):
    hist_list = database.login_history()
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(
        ['Имя Клиента', 'Последний раз входил', 'IP', 'Port'])
    for row in hist_list:
        user, last_seen, IP, Port = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        IP = QStandardItem(str(IP))
        IP.setEditable(False)
        Port = QStandardItem(str(Port))
        Port.setEditable(False)
        list_table.appendRow([user, last_seen, IP, Port])
    return list_table


@Log(_logger)
def _parse_args():
    parser = argparse.ArgumentParser(description="Messenger client")
    parser.add_argument(
        '--port',
        '-p',
        type=port,
        required=False,
        default=DEFAULT_PORT,
        help='server port.'
    )

    parser.add_argument(
        '--server_address',
        '-a',
        type=server_ip,
        required=False,
        default='0.0.0.0',
        help='server ip address.',
    )
    args = parser.parse_args()
    return args


class Port:
    def __init__(self, value=7777):
        self._value = value

    def __get__(self, instance, instance_type):
        return self._value

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError("Int type required")
        if not 1024 <= value <= 49151:
            raise argparse.ArgumentTypeError(f'port must be in range [1024,49151]')
        self._value = value


class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        is_sock_stream = False

        for key, value in clsdict.items():
            if isinstance(value, socket.socket):
                raise TypeError(f"Don't create socket in class!")
            if value != 'Port':
                try:
                    instrs = dis.get_instructions(value)
                    for instr in instrs:
                        if instr.argval == 'socket':
                            _next_instr = next(instrs)
                            if _next_instr.argval == 'SOCK_STREAM':
                                is_sock_stream = True
                            if _next_instr.argval == 'connect':
                                raise TypeError(f"Call connect in server!")
                except TypeError:
                    pass
        if not is_sock_stream:
            raise TypeError(f"Use SOCK_STREAM!")
        type.__init__(self, clsname, bases, clsdict)


class Server(threading.Thread, metaclass=ServerVerifier):
    _port = Port()

    def __init__(self, database, server_port, server_address):
        self.database = database
        try:
            _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._port = server_port
            _server_socket.bind((server_address, self._port))

            _server_socket.listen(MAX_CONNECTIONS)
            _server_socket.settimeout(0.5)
        except Exception as e:
            print("server start failed", e)
            sleep(10)
            raise e
        self.server_socket = _server_socket
        _logger.info(f'server start at {server_address}:{self._port}')
        print(f'server start at {server_address}:{self._port}')
        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

    @Log(_logger)
    def process_client_message(self, message, client):
        """
        Validate message from client
        :param client:
        :param message:
        :return:
        """
        global active_clients_changed
        _logger.debug(f'Message from client: {message}')
        if ACTION in message and \
                message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.client_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    active_clients_changed = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'username is used'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and TIME in message \
                and USER_LOGIN in message:
            self.get_contacts(message)
            return
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT or message[ACTION] == DEL_CONTACT \
                and USER_ID in message \
                and TIME in message \
                and USER_LOGIN in message:
            self.create_delete_contacts(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            try:
                self.database.client_logout(message[ACCOUNT_NAME])

                self.clients.remove(self.names[message[ACCOUNT_NAME]])
                self.names[message[ACCOUNT_NAME]].close()
                del self.names[message[ACCOUNT_NAME]]
                with conflag_lock:
                    active_clients_changed = True
            except:
                pass
            try:
                self.names.pop(message[ACCOUNT_NAME]).close()
            except:
                pass
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request'
            send_message(client, response)
            return

    def run(self):
        while True:
            try:
                conn, client_address = self.server_socket.accept()
            except Exception:
                pass
            else:
                self.clients.append(conn)
                _logger.info(f'connection complete {client_address}')
                print(f'connection complete {client_address}')

            rlist = []
            wlist = []
            try:
                if self.clients:
                    rlist, wlist, _ = select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if rlist:
                for _client in rlist:
                    try:
                        self.process_client_message(get_message(_client), _client)
                    except (ConnectionResetError, JSONDecodeError):
                        _logger.info(f'{_client} disconnected.')
                        self.clients.remove(_client)

            if self.messages and wlist:
                _msg = self.messages.pop()
                print(f'current message: {_msg}')
                message = {
                    ACTION: MESSAGE,
                    SENDER: _msg[SENDER],
                    DESTINATION: _msg[DESTINATION],
                    TIME: time(),
                    MESSAGE_TEXT: _msg[MESSAGE_TEXT]
                }
                for waiting_client in wlist:
                    try:
                        send_message(waiting_client, message)
                        print(f'message sent: {message}')
                    except:
                        _logger.info(f'{waiting_client} disconnected.')
                        print(f'{waiting_client} disconnected.')
                        self.clients.remove(waiting_client)

                for i in self.messages:
                    try:
                        if message[DESTINATION] in self.names \
                                and self.names[message[DESTINATION]] in wlist:
                            send_message(self.names[message[DESTINATION]], message)
                            _logger.info(f'{message[SENDER]} send message to {message[DESTINATION]}')
                        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in wlist:
                            raise ConnectionError
                        else:
                            _logger.error(
                                f'bad user {message[DESTINATION]}')
                    except Exception:
                        _logger.info(f'connection with {i[DESTINATION]} lost')
                        self.clients.remove(self.names[i[DESTINATION]])
                        self.names.pop(i[DESTINATION])
                self.messages.clear()

    def get_contacts(self, message):
        resp = self.database.get_contacts(message[USER_LOGIN])
        message = {
            RESPONSE: RESPONSE_202,
            ALERT: resp
        }
        send_message(self.server_socket, message)

    def create_delete_contacts(self, message):
        if message[ACTION] == ADD_CONTACT:
            resp = self.database.add_contact(message[USER_ID], message[USER_LOGIN])
        else:
            resp = self.database.delete_contact(message[USER_ID], message[USER_LOGIN])
        message = {
            RESPONSE: resp,
        }
        send_message(self.server_socket, message)


class Stats(QDialog):
    def __init__(self, parent=None):
        super(Stats, self).__init__(parent)
        Form, Base = uic.loadUiType('statistics.ui', self)
        self.ui = Form()
        self.ui.setupUi(self)


if __name__ == '__main__':
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    db = ServerDB(config['SETTINGS']['Database_file'])
    server = Server(db, int(config['SETTINGS']['Default_port']), config['SETTINGS']['Listen_Address'])
    server.daemon = True
    server.start()
    app = QtWidgets.QApplication(sys.argv)
    window = uic.loadUi('gui.ui')
    window.show()

    def save_server_config():
        message = QMessageBox()
        config['SETTINGS']['database_file'] = settings_window.dbFile.text()
        config['SETTINGS']['default_port'] = str(settings_window.port.text())
        with open('server.ini', 'w') as conf:
            config.write(conf)
            message.information(
                settings_window, 'OK', 'Настройки успешно сохранены!')

    def list_update():
        global active_clients_changed
        if active_clients_changed:
            window.clientsTable.setModel(
                gui_create_model(db))
            window.clientsTable.resizeColumnsToContents()
            window.clientsTable.resizeRowsToContents()
            with conflag_lock:
                active_clients_changed = False

    def show_settings():
        settings_window.show()
        settings_window.dbFile.clear()
        settings_window.dbFile.insert(config['SETTINGS']['database_file'])
        settings_window.port.setValue(int(config['SETTINGS']['default_port']))
        settings_window.listen_address.insert(config['SETTINGS']['listen_address'])

        def open_file():
            file, _ = QFileDialog.getOpenFileName(None, 'Open File', options=QFileDialog.DontResolveSymlinks)
            if file:
                settings_window.dbFile.clear()
                settings_window.dbFile.insert(file)
        settings_window.dbFileOpenButton.clicked.connect(open_file)
        settings_window.buttonBox.accepted.connect(save_server_config)


    def show_statistics():
        stats.show()
        stats.ui.statisticsTable.setModel(create_stat_model(db))


    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)
    window.actionRefresh.triggered.connect(list_update)
    settings_window = uic.loadUi('settings.ui')
    window.actionSettings.triggered.connect(show_settings)
    stats = Stats()
    window.actionStatistics.triggered.connect(show_statistics)

    sys.exit(app.exec_())
