"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport
    history = []

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login not in self.server.clients_logins:
                    self.send_history()
                    self.transport.write(
                        f"\n <console> Hi, {self.login}!".encode()
                    )
                    self.server.clients_logins.append(self.login)
                else:
                    self.transport.write(
                        f"login: {self.login} already taken! Try another".encode()
                    )
                    self.transport.close()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        format_string_save = format_string + "\n"
        encoded = format_string.encode()
        encoded_save = format_string_save.encode()
        self.history.append(encoded_save)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        while len(self.history) > 10:
            self.history = self.history[1:]

        for item in self.history:
            for client in self.server.clients:
                if client.login == self.login:
                    client.transport.write(item)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Connection established")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Connection lost")


class Server:
    clients: list
    clients_logins: list

    def __init__(self):
        self.clients = []
        self.clients_logins = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Server is running ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server stopped manually")
