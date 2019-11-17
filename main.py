from PyQt5.QtWidgets import *
import PyQt5.QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel
import sqlite3
from hashlib import sha256


class Login(QDialog):
    def __init__(self):
        self.token = None
        super().__init__(None, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Authorization")
        self.textLogin = QLineEdit()
        self.textPassw = QLineEdit()
        self.textPassw.setEchoMode(QLineEdit.Password)
        button = QPushButton("Login")
        button.clicked.connect(self.handle_login)
        layout = QVBoxLayout(self)
        layout.addWidget(self.textLogin)
        layout.addWidget(self.textPassw)
        layout.addWidget(button)
        self.setWindowFlag(Qt.MSWindowsFixedSizeDialogHint)
        # self.resize(self.sizeHint())

    def handle_login(self):
        username = self.textLogin.text()
        connection = sqlite3.connect("users.sqlite")
        query = "SELECT username FROM users WHERE username=? and password_hash=?;"
        params = (username, sha256(self.textPassw.text().encode()).hexdigest())
        result = connection.execute(query, params).fetchall()
        connection.close()
        if len(result) != 0:
            self.token = username
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Bad login or pass")


class people_InsertWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        VBoxLayout = QVBoxLayout()

        HBoxLayout = QHBoxLayout()
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Full name")
        self.telephone = QLineEdit()
        self.telephone.setPlaceholderText("Telephone")
        self.submit_button = QPushButton("INSERT INTO people")

        HBoxLayout.addWidget(self.full_name)
        HBoxLayout.addWidget(self.telephone)

        VBoxLayout.addLayout(HBoxLayout)
        VBoxLayout.addWidget(self.submit_button)
        self.setLayout(VBoxLayout)


class addresses_InsertWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        VBoxLayout = QVBoxLayout(self)

        self.user_id = QLineEdit()
        self.user_id.setPlaceholderText("Person id")
        self.street = QLineEdit()
        self.street.setPlaceholderText("Street")
        self.city = QLineEdit()
        self.city.setPlaceholderText("City")
        self.state = QLineEdit()
        self.state.setPlaceholderText("State")
        self.submit_button = QPushButton("INSERT INTO addresses")

        VBoxLayout.addWidget(self.user_id)
        VBoxLayout.addWidget(self.street)
        VBoxLayout.addWidget(self.city)
        VBoxLayout.addWidget(self.state)
        VBoxLayout.addWidget(self.submit_button)
        self.setLayout(VBoxLayout)


class MainWindow(QWidget):
    def __init__(self, token: str):
        connection = sqlite3.connect("users.sqlite")
        query = """
        SELECT
            privileges.privilege
        FROM
            privileges
            JOIN users ON privileges.username = users.username
        WHERE
            users.username = ?;
        """
        self.privileges = set(_[0] for _ in connection.execute(query, (token,)).fetchall())
        connection.close()
        super().__init__()
        self.setWindowTitle("CSM")
        tabs = QTabWidget()
        if "SELECT" in self.privileges:
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName("data.sqlite")
            db.open()

            if any(privilege in self.privileges for privilege in ("UPDATE", "INSERT", "DELETE")):
                self.people_model = QSqlTableModel()
                self.people_model.setTable("people")
                if "UPDATE" in self.privileges:
                    self.people_model.setEditStrategy(QSqlTableModel.OnFieldChange)
                self.people_model.select()

                self.addresses_model = QSqlTableModel()
                self.addresses_model.setTable("addresses")
                if "UPDATE" in self.privileges:
                    self.addresses_model.setEditStrategy(QSqlTableModel.OnFieldChange)
                self.addresses_model.select()
            else:
                self.people_model = QSqlQueryModel()
                self.people_model.setQuery("SELECT * FROM people;")

                self.addresses_model = QSqlQueryModel()
                self.addresses_model.setQuery("SELECT * FROM addresses;")

            self.people_model.setHeaderData(1, Qt.Horizontal, "Full name")
            self.people_model.setHeaderData(2, Qt.Horizontal, "Telephone")

            self.addresses_model.setHeaderData(1, Qt.Horizontal, "Person id")
            self.addresses_model.setHeaderData(2, Qt.Horizontal, "Street")
            self.addresses_model.setHeaderData(3, Qt.Horizontal, "City")
            self.addresses_model.setHeaderData(4, Qt.Horizontal, "State")

            self.people_table = QTableView()
            self.people_table.setModel(self.people_model)
            if "UPDATE" not in self.privileges:
                self.people_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.people_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.people_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.people_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.people_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            self.people_table.resizeColumnsToContents()

            self.addresses_table = QTableView()
            self.addresses_table.setModel(self.addresses_model)
            if "UPDATE" not in self.privileges:
                self.addresses_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.addresses_table.hideColumn(0)
            self.addresses_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.addresses_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.addresses_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            self.addresses_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
            self.addresses_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            self.addresses_table.resizeColumnsToContents()

            self.people_table.setMinimumWidth(self.people_table.width())
            self.addresses_table.setMinimumWidth(self.addresses_table.width())

            tabs.addTab(self.people_table, "People")
            tabs.addTab(self.addresses_table, "Addresses")
            tabs.currentChanged.connect(self.tab_switch_handler)

        HLayout = QHBoxLayout(self)
        HLayout.addWidget(tabs)

        self.VLayout = QVBoxLayout()
        self.VLayout.setAlignment(Qt.AlignTop)
        token_label = QLabel(token)
        self.VLayout.addWidget(token_label)

        if "INSERT" in self.privileges:
            self.insert_stack = QStackedWidget()
            self.people_insert = people_InsertWidget()
            self.people_insert.submit_button.clicked.connect(self.insert_people_handler)

            self.addresses_insert = addresses_InsertWidget()
            self.addresses_insert.submit_button.clicked.connect(self.insert_address_handler)

            self.insert_stack.addWidget(self.people_insert)
            self.insert_stack.addWidget(self.addresses_insert)
            self.insert_stack.setCurrentWidget(self.people_insert)
            self.insert_stack.setFixedSize(self.insert_stack.sizeHint())
            self.VLayout.addWidget(self.insert_stack)

        self.VLayout.addSpacing(10)

        if "DELETE" in self.privileges:
            self.delete_stack = QStackedWidget()

            self.people_delete = QPushButton("DELETE FROM people")
            self.people_delete.clicked.connect(self.delete_people_handler)

            self.address_delete = QPushButton("DELETE FROM addresses")
            self.address_delete.clicked.connect(self.delete_address_handler)

            self.delete_stack.addWidget(self.people_delete)
            self.delete_stack.addWidget(self.address_delete)
            self.delete_stack.setCurrentWidget(self.people_delete)
            self.delete_stack.setFixedSize(self.delete_stack.sizeHint())
            self.VLayout.addWidget(self.delete_stack)

        HLayout.addLayout(self.VLayout)
        #self.resize(self.sizeHint())

    def tab_switch_handler(self, tab: int):
        if tab == 0:
            if "INSERT" in self.privileges:
                self.insert_stack.setCurrentWidget(self.people_insert)
            if "DELETE" in self.privileges:
                self.delete_stack.setCurrentWidget(self.people_delete)
        elif tab == 1:
            if "INSERT" in self.privileges:
                self.insert_stack.setCurrentWidget(self.addresses_insert)
            if "DELETE" in self.privileges:
                self.delete_stack.setCurrentWidget(self.address_delete)
        else:
            QMessageBox.warning(self, "Error", "Something went wrong!")

    def insert_people_handler(self):
        full_name = self.people_insert.full_name.text()
        telephone = self.people_insert.telephone.text()
        record = self.people_model.record()
        record.setGenerated("id", True)
        record.setValue("full_name", full_name)
        record.setValue("telephone", telephone)
        if self.people_model.insertRecord(-1, record):
            self.people_model.select()
        else:
            QMessageBox.warning(self, "Error", "Cannot insert {} {}".format(full_name, telephone))

    def insert_address_handler(self):
        user_id = int(self.addresses_insert.user_id.text())
        street = self.addresses_insert.street.text()
        city = self.addresses_insert.city.text()
        state = self.addresses_insert.state.text()
        record = self.addresses_model.record()
        record.setGenerated("id", True)
        record.setValue("user_id", user_id)
        record.setValue("street", street)
        record.setValue("city", city)
        record.setValue("state", state)
        if self.addresses_model.insertRecord(-1, record):
            self.addresses_model.select()
        else:
            QMessageBox.warning(self, "Error", "Cannot insert {} {} {} {}".format(user_id, street, city, state))

    def delete_people_handler(self):
        rows = self.people_table.selectionModel().selectedRows()
        if len(rows) == 1:
            if not self.people_model.removeRow(rows[0].row()):
                QMessageBox.warning(self, "Error", "Cannot delete row {}".format(rows[0].row()+1))
            else:
                self.people_model.select()
        else:
            QMessageBox.warning(self, "Error", "Only 1 row can be deleted at a time")

    def delete_address_handler(self):
        rows = self.addresses_table.selectionModel().selectedRows()
        if len(rows) == 1:
            if not self.addresses_model.removeRow(rows[0].row()):
                QMessageBox.warning(self, "Error", "Cannot delete row {}".format(rows[0].row() + 1))
            else:
                self.addresses_model.select()
        else:
            QMessageBox.warning(self, "Error", "Only 1 row can be deleted at a time")


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    login = Login()
    if login.exec_() == QDialog.Accepted:
        main = MainWindow(login.token)
        main.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
