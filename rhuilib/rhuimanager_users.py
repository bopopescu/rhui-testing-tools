from rhuilib.expect import *
from rhuilib.rhuimanager import *


class RHUIManagerUsers:
    @staticmethod
    def change_password(connection, username, password):
        RHUIManager.screen(connection, "users")
        Expect.enter(connection, "p")
        Expect.expect(connection, "Username:")
        Expect.enter(connection, username)
        Expect.expect(connection, "New Password:")
        Expect.enter(connection, password)
        Expect.expect(connection, "Re-enter Password:")
        Expect.enter(connection, password)
        Expect.expect(connection, "Password successfully updated.*rhui \(users\) =>")
        Expect.enter(connection, "q")
