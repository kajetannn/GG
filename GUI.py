import tkinter
import socket
import time
from tkinter import messagebox

port=8080
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.settimeout(0.5)
#lista przechowujaca wiadomosci z poszczegolnymi uzytkownikami
messages = []
#lista przechowujaca innych uzytkownikow
users = []
#okienko sluzace do logowania
def login():

    def log():
        #pobierz z pol tekstowych nick oraz ip serwera
        name = username.get()
        server = ip.get()
        try:
            if "/" in name:
                l5 = tkinter.Label(f, text="Nick nie moze zawierac znaku /".format(name), font='helvetica 10 bold', bg="white")
                l5.place(x=120, y=230)
                raise Exception
            elif name == "":
                l5 = tkinter.Label(f, text="Nick nie moze byc pusty".format(name), font='helvetica 10 bold', bg="white")
                l5.place(x=120, y=230)
                raise Exception
            elif len(name) > 15:
                l5 = tkinter.Label(f, text="Nick nie moze miec powyzej 15 znakow".format(name), font='helvetica 10 bold', bg="white")
                l5.place(x=120, y=230)
                raise Exception
            connection.connect((server, port))
            message = "L/" + name + "/"
            connection.send(message.encode("utf-8"))
            time.sleep(2)
            window.destroy()
            app(name)
        except Exception:
            l4 = tkinter.Label(f, text="Blad logowania".format(name), font='helvetica 10 bold', bg="white")
            l4.place(x=120, y=210)

    #utworzenie okienka i dodanie do niego elementow
    window = tkinter.Tk()
    f = tkinter.Frame(window, bg="white", width=400, height=400)
    f.grid(row=0, column=0, sticky="NW")
    f.grid_propagate(0)
    f.update()
    window.title("Sign in / Sign up")
    window.geometry("400x400")

    l1 = tkinter.Label(f, text="LOGOWANIE", font='helvetica 18 bold', bg="white")
    l1.place(x=120, y=80)
    l2 = tkinter.Label(f, text="Nick", font='helvetica 12 bold', bg="white")
    l2.place(x=80, y=118)
    l3 = tkinter.Label(f, text="IP serwera", font='helvetica 12 bold', bg="white")
    l3.place(x=40, y=150)

    username = tkinter.StringVar()
    ip = tkinter.StringVar()
    e = tkinter.Entry(f, textvariable = username, width=24)
    e.place(x=125, y=120)
    e2 = tkinter.Entry(f, textvariable=ip, width=24)
    e2.place(x=125, y=150)
    b = tkinter.Button(f, text="Zaloguj", font='helvetica 10', height=1, width=17, command=lambda : log())
    b.place(x=125, y=180)
    window.mainloop()

#okno sluzace do wyboru czatu
def app(username):
    def logout(name):
        message = "W/" + name + "/"
        connection.send(message.encode("utf-8"))
        tkinter.messagebox.showinfo("GG - {}".format(username), "Wylogowano")
        window.destroy()

    def refresh(username):
        window.destroy()
        app(username)

    def conversation(usr1):
        #pobierz z listy uzytkownika, z ktorym chcesz czatowac
        name = var.get()
        window.destroy()
        chat(usr1, name)

    #funkcja dodajaca do listy messages wszystkie odebrane wiadomosci
    def handleList(message):
        message = message.split("/")
        cond = 1
        for i in range(len(message)):
            if message[i] == "M":
                for j in range(len(messages)):
                    if messages[j][0] == message[i+2]:
                        messages[j].append((message[i + 1], message[i + 2], message[i + 3]))
                        cond = 0
                if cond == 1:
                    messages.append([message[i+2]])
                    messages[-1].append((message[i + 1], message[i + 2], message[i + 3]))


    window = tkinter.Tk()
    #po zalogowaniu wyslij do serwera prosbe o liste ze wszystkimi uzytkownikami
    msg = "U/" + username + "/"
    connection.send(msg.encode("utf-8"))
    res = connection.recv(256).decode("utf-8")
    # jezeli do odebrania czekaja juz jakies wiadomosci, dodaj je do listy messages
    if res[0:2] == 'M/':
        handleList(res)
        msg = "U/" + username + "/"
        connection.send(msg.encode("utf-8"))
        res = connection.recv(256).decode("utf-8")

    #po odebraniu wiadomosci z uzytkownikami dodaj wszystkie potrzebne informacje do list messages oraz users
    res = res.replace("\x00","___")
    res = res.split("___")[0]
    res = res.split(",")
    for el in res:
        if len(el) > 0:
            if el[0] != "" and el[0:2] != "M/" and el != username:
                if el not in users:
                    users.append(el)
                    messages.append([el])

            elif el[0:1] == "M/":
                handleList(el)

    #utworzenie okna do wyboru czatu i dodanie potrzebnych elementow
    f = tkinter.Frame(window, bg="white", width=600, height=500)
    f.grid(row=0, column=0, sticky="NW")
    f.grid_propagate(0)
    f.update()
    window.title("GG - {}".format(username))
    window.geometry("600x500")

    l1 = tkinter.Label(f, text="Dostępne czaty", font='helvetica 18 bold', bg="white")
    l1.place(x=120, y=80)
    l2 = tkinter.Label(f, text="Nick", font='helvetica 12 bold', bg="white")
    l2.place(x=80, y=118)

    b = tkinter.Button(f, text="Wyloguj", font='helvetica 10 bold', height=1, width=17, command=lambda: logout(username))
    b.place(x=450, y=450)
    b2 = tkinter.Button(f, text="Odśwież", font='helvetica 10 bold', height=1, width=17, command=lambda: refresh(username))
    b2.place(x=450, y=400)
    b3 = tkinter.Button(f, text="Przejdź do czatu", font='helvetica 10 bold', height=1, width=17, command=lambda: conversation(username))
    b3.place(x = 125, y = 150, width = 200)
    var = tkinter.StringVar(f)
    #wczytanie do listy rozwijanej nickow uzytkownikow z bazy
    if len(users) > 0:
        var.set(users[0])
        o = tkinter.OptionMenu(f, var, *users)
        o.place(x = 125, y = 120, width = 250)
    else:
        l3 = tkinter.Label(f, text="Brak innych uzytkownikow w bazie :(", font='helvetica 12 bold', bg="white")
        l3.place(x=125, y=118)
    window.mainloop()

#okienko odpowiedzialne za rozmowe z innym uzytkownikiem
def chat(usr1, usr2):
    #powrot do poprzedniego okienka
    def menu(user):
        window.destroy()
        app(user)
    #odswiezenie czatu
    def refresh(us1, us2):
        window.destroy()
        chat(us1,us2)
        show_msg()
    #wyslanie wiadomosci do uzytkownika
    def send_msg(receiver,sender):
        msg = "M/{}/{}/{}/".format(receiver,sender,message.get())
        connection.send(msg.encode("utf-8"))
        for i in range(len(messages)):
            if messages[i][0] == receiver:
                messages[i].append((receiver, sender, message.get()))
        show_msg()
    #wczytanie do listy messages odebranych wiadomosci
    def handleList(message):
        message = message.split("/")
        cond = 1
        for i in range(len(message)):
            if message[i] == "M":
                for j in range(len(messages)):
                    if messages[j][0] == message[i + 2]:
                        messages[j].append((message[i + 1], message[i + 2], message[i + 3]))
                        cond = 0
                if cond == 1:
                    messages.append([message[i + 2]])
                    messages[-1].append((message[i + 1], message[i + 2], message[i + 3]))

    #funkcja odpowiedzialna za wyswietlenie na ekranie wszystkich wiadomosci z danym uzytkownikiem
    #funkcja wywoluje sama siebie co 7 sekund, by czat odswiezal sie automatycznie
    def show_msg():
        try:
            msg = connection.recv(256).decode("utf-8")
            handleList(msg)
            for i in range(len(messages)):
                if messages[i][0] == usr2:
                    if len(messages[i]) == 19:
                        messages[i][1:] = messages[i][2:19]
                    if len(messages[i]) > 1:
                        for j in range(1,len(messages[i])):
                            if (messages[i][j][0] == usr2 and messages[i][j][1] == usr1) or (messages[i][j][0] == usr1 and messages[i][j][1] == usr2):
                                tkinter.Label(text = messages[i][j][1] + ": " + messages[i][j][2],font='helvetica 10 bold', width = 500, anchor = "w").place(x = 0, y = 20*(j-1))
                        break
        except Exception:
            for i in range(len(messages)):
                if messages[i][0] == usr2:
                    if len(messages[i]) == 19:
                        messages[i][1:] = messages[i][2:19]
                    if len(messages[i]) > 1:
                        for j in range(1, len(messages[i])):
                            if (messages[i][j][0] == usr2 and messages[i][j][1] == usr1) or (messages[i][j][0] == usr1 and messages[i][j][1] == usr2):
                                tkinter.Label(text=messages[i][j][1] + ": " + messages[i][j][2],font='helvetica 10 bold', width=500, anchor="w").place(x=0, y=20 * (j-1))
                        break
        window.after(7000, show_msg)

    # utworzenie okna do wyboru czatu i dodanie potrzebnych elementow
    window = tkinter.Tk()
    f = tkinter.Frame(window, bg="white", width=600, height=350)
    f2 = tkinter.Frame(window,width = 600, height = 150)
    f.grid(row=0, column=0, sticky="NW")
    f.grid_propagate(0)
    f.update()
    f2.grid(row=1, column=0, sticky="NW")
    f2.grid_propagate(0)
    f2.update()
    window.title("Czat - {} - {}".format(usr1,usr2))
    window.geometry("600x500")
    show_msg()
    message = tkinter.StringVar()
    e = tkinter.Entry(f2, textvariable=message, font = 8, width=70)
    e.place(x=5, y=5)

    b2 = tkinter.Button(f2, text="Odswiez", font='helvetica 10 bold', height=1, width=20, command=lambda: refresh(usr1, usr2))
    b2.place(x=400, y=50)
    b3 = tkinter.Button(f2, text="Wyslij", font='helvetica 10 bold', height=1, width=20,command=lambda: [send_msg(usr2,usr1), e.delete(0,"end")])
    b3.place(x=5, y=50)
    b4 = tkinter.Button(f2, text="Menu", font='helvetica 10 bold', height=1, width=20,command=lambda: [menu(usr1), window.after_cancel(window)])
    b4.place(x=400, y=80)
    window.mainloop()


def main():
    login()