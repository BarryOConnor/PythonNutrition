# The code for changing pages was derived from: http://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
# The code for switching menu bars was derived from: https://stackoverflow.com/questions/37621071/tkinter-add-menu-bar-in-frames
# The code for creating the stacked bar chart was derived from: https://matplotlib.org/gallery/lines_bars_and_markers/bar_stacked.html
# License: http://creativecommons.org/licenses/by-sa/3.0/	

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as ms
from datetime import datetime
import sqlite3, json, os, math, numpy
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure



class pyNutrition(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        self.geometry("500x600") # set window to 500x600
        self.title("Python Nutrition")# set window title

        style = ttk.Style()
        style.configure("Treeview.Heading", foreground="#9E7BB8")


        self.welcome = tk.StringVar() #setup a variable linked to the welcome label, so it displays username after login
        #dictionary of info about the current user. populated upon login
        self.current_user = {"id" : "", "username" : "", "password" : "", "birthday" : "", "height" : "", "weight" : "", "calories" : "", "protein" : "", "carbs" : "", "fat" : ""}

        #setup a list of years for use in the program"s DOB fields.
        self.days = []
        for i in range(1,32):
            self.days.append(str(i).zfill(2)) #format to 2 characters just so each date is equal length

        #setup a list of months for use in the program"s DOB fields.
        self.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        #setup a dictionary mapping the months to their numerical value, just so that it"s user friendly and database friendly
        self.month_mapping = {"January":"01", "February":"02", "March":"03", "April":"04", "May":"05", "June":"06", "July":"07", "August":"08", "September":"09", "October":"10", "November":"11", "December":"12"}

        #setup a list of years for use in the program"s DOB fields. Taken that most people won"t be older than 100 years old
        self.years = []
        for i in range(datetime.now().year,datetime.now().year - 111,-1):
            self.years.append(str(i))
            
        self.logo = tk.PhotoImage(file="images/logo.gif") # load logo
        lbl_logo=tk.Label(self, image=self.logo)# set logo into label
        lbl_logo.place(y=0, x=0, width=500, height=143)# place the label

        container = tk.Frame(self) #create a container for all the different forms (frames)
        container.place(y=143, x=0, width=500, height=957) #place under the logo so only this frame changes

        #Setup database just in case there isn"t one available
        with sqlite3.connect("python_nutrition.db") as db:
                c = db.cursor()
                sql_statement = ("""CREATE TABLE IF NOT EXISTS `food_diary` (
                                    `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    `date`	NUMERIC NOT NULL,
                                    `food_name`	TEXT NOT NULL,
                                    `food_weight`	REAL NOT NULL,
                                    `calories`	REAL NOT NULL,
                                    `protein`	REAL NOT NULL,
                                    `carbs`	REAL NOT NULL,
                                    `fat`	REAL NOT NULL
                                );""")
                c.execute(sql_statement)
                db.commit()
                sql_statement = ("""CREATE TABLE IF NOT EXISTS `users` (
                                    `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    `username`	TEXT NOT NULL,
                                    `password`	TEXT NOT NULL,
                                    `birthday`	NUMERIC NOT NULL DEFAULT 01012000,
                                    `weight`	REAL NOT NULL,
                                    `height`	REAL NOT NULL,
                                    `calories`	REAL NOT NULL DEFAULT 1994,
                                    `protein`	REAL NOT NULL DEFAULT 205,
                                    `carbs`	REAL NOT NULL DEFAULT 145,
                                    `fat`	REAL NOT NULL DEFAULT 66
                                );""")
                c.execute(sql_statement)
                db.commit()


        menubar = tk.Menu(container)
        tk.Tk.config(self, menu=menubar)
        fileMenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=fileMenu)
        fileMenu.add_command(label="Exit", command=quit)

        self.frames = {}

        for F in (LoginPage, RegisterUser, EditProfile, MainScreen, FoodDiary):
            #setup all the identical frames in this loop
            frame = F(container, self)
            self.frames[F] = frame
            frame.place(y=0, x=0, width=500, height=957)
            

        self.show_frame(LoginPage) #load the login page by default



    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()
        frame.event_generate("<<showframe>>")
        menubar = frame.menubar(self)
        self.configure(menu=menubar)


    @staticmethod    
    def export_food_diary(self):
        #export the food diary
        with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            sqlstring = """SELECT id, date, user_id, food_name, food_weight, calories, protein, carbs, fat FROM food_diary WHERE `user_id` = ? ORDER BY `date`, `food_name` ASC"""
            export_diary = (sqlstring)

            c.execute(export_diary,[(self.current_user["id"])])
            rows = c.fetchall()
            diary = []
            for row in rows:
                food = {
                    'id' : row[0],
                    'date' : row[1],
                    'user_id' : row[2],
                    'food_name' : row[3],
                    'food_weight' : row[4],
                    'calories' : row[5],
                    'protein' : row[6],
                    'carbs' : row[7],
                    'fat' : row[8],
                }
                diary.append(food)

        export_filename = self.current_user["username"] +"_"+ str(datetime.now().day).zfill(2) + str(datetime.now().month).zfill(2) + str(datetime.now().year) +".bak"
        if os.path.exists(export_filename):
            os.remove(export_filename)
        export_file = open(export_filename, "w")
        export_file.write(json.dumps(diary))              
        export_file.close()
        if os.path.exists(export_filename):
            ms.showinfo("Export Complete", "Your diary has been exported")
        else:
            ms.showerror("Export Error", "An error occurred")                   

#the following database commands are easier to handle on the controller - only one place needs to be changed if the tables change

    @staticmethod    
    def delete_record_from_table(self, param_table, param_id, param_title, param_message, param_redirect=False):
        #Only 2 tables currently and deletion only needs a table name and an ID so it's quicker as a function centrally
        if ms.askyesno(param_title, param_message) == True:
            with sqlite3.connect("python_nutrition.db") as db:
                c = db.cursor()
                delete_statement = ("DELETE FROM "+param_table+" WHERE id = ?")
                c.execute(delete_statement,[(param_id)])
                db.commit()
                if param_redirect != False:
                    self.show_frame(param_redirect)

                    
    @staticmethod  
    def insert_new_user(self, username, password, birthday, weight, height, calories, protein, carbs, fat):
        #Create a new user account
        with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            #Insert SQL statement with ? for parameter insertion (sqlite3 protects against insertion attacks with this)
            create_user = ("INSERT into users (`username`, `password`, `birthday`, `weight`, `height`, `calories`, `protein`, `carbs`, `fat`)VALUES(?,?, ?, ?, ?, ?, ?, ?, ?)")
            c.execute(create_user,[(username),(password),(birthday),(weight),(height),(calories),(protein),(carbs),(fat)]) #populate the query parameters
            result = c.lastrowid #lastrowid stores the new record ID, if set, the query was successful
            if result > 0:
                ms.showinfo("Info","New account has been successfully created. Please login")
                return True #successful
            else:
                ms.showerror("Error","Registration was not successful, please recheck your answers.")
                return False
            
    @staticmethod  
    def update_current_user(self, username, password, birthday, weight, height, calories, protein, carbs, fat):
        #Update an existing user account
         with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            #Insert SQL statement with ? for parameter insertion 
            create_user = ("UPDATE users SET `username` = ?, `password` = ?, `birthday` = ?, `weight` = ?, `height` = ?, `calories` = ?, `protein` = ?, `carbs` = ?, `fat` = ? WHERE id = ?")
            c.execute(create_user,[(username),(password),(birthday),(weight),(height),(calories),(protein),(carbs),(fat),self.controller.current_user["id"]])#populate the query parameters
            result = c.rowcount #rowcount stores the number of updated rows, if greater then 0, the query was successful
            if result > 0:
                ms.showinfo("Info","Your Account details have been successfully updated")
                return True #successful
            else:
                ms.showerror("Error","Unable to update your Account, please recheck your answers.")
                return False
                    
    @staticmethod  
    def insert_new_food(self, food_name, weight, calories, protein, carbs, fat):
        #Create a new user account
        with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            #Insert SQL statement with ? for parameter insertion (sqlite3 protects against insertion attacks with this)
            create_user = ("INSERT INTO food_diary (`date`, `user_id`, `food_name`, `food_weight`, `calories`, `protein`, `carbs`, `fat`) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
            currdate = str(datetime.now().day).zfill(2) +"-"+ str(datetime.now().month).zfill(2) +"-"+ str(datetime.now().year)
            c.execute(create_user,[(currdate),self.controller.current_user["id"],(food_name),(weight),(calories),(protein),(carbs),(fat)]) #populate the query parameters
            result = c.lastrowid #lastrowid stores the new record ID, if set, the query was successful
            if result > 0:
                ms.showinfo("Info","New food has been successfully added.")
                return True #successful
            else:
                ms.showerror("Error","Food addition was not sucessful, please recheck your answers.")
                return False
            
    @staticmethod  
    def update_existing_food(self, food_name, weight, calories, protein, carbs, fat, food_id):
        #Update an existing user account
         with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            #Insert SQL statement with ? for parameter insertion 
            create_user = ("UPDATE food_diary SET `user_id` = ?, `food_name` = ?, `food_weight` = ?, `calories` = ?, `protein` = ?, `carbs` = ?, `fat` = ? WHERE id = ?")
            c.execute(create_user,[self.controller.current_user["id"],(food_name),(weight),(calories),(protein),(carbs),(fat),(food_id)])#populate the query parameters
            result = c.rowcount #rowcount stores the number of updated rows, if greater then 0, the query was successful
            if result > 0:
                ms.showinfo("Info","Food has been successfully updated.")
                return True #successful
            else:
                ms.showerror("Error","Unable to update Food, please recheck your answers.")
                return False
                    


    @staticmethod
    def check_date(self, param_day, param_month, param_year):
        #used to check the given day month and year combo are valid

        if param_day!="" and param_year!="" and param_month!="": #stops code running multiple times on init updates to comboboxes
            try:       
                datetime.strptime(str(param_day)+"-"+self.month_mapping[str(param_month)]+"-"+str(param_year),"%d-%m-%Y")
                return True
            except ValueError:
                ms.showerror("Warning","The date you have chosen is not correct.")
                return False





class LoginPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        self.controller = controller #sets the controller to be referenced in the instance so you can use it again later
        self.bind("<Return>", self.login)
        self.focus_set()

        #setup controls for this frame
        self.lbl_title = tk.Label(self, text="Login", font=("Verdana", 14), bg="#9E7BB8", fg="white")
        self.lbl_title.place(y=0, x=0, width=500)
        
        self.lbl_name = tk.Label(self, width=10, anchor=tk.NE,  text="Name")
        self.lbl_name.place(y=70, x=115, width=60)
        self.lbl_password = tk.Label(self, width=10, anchor=tk.E,  text="Password")
        self.lbl_password.place(y=100, x=115, width=60)

        self.txt_username = tk.Entry(self, width=30)    
        self.txt_username.place(y=70, x=185, anchor=tk.NW, width=200)
        self.txt_password = tk.Entry(self, width=30,show="*")
        self.txt_password.place(y=100, x=185, anchor=tk.NW, width=200)

        self.btn_register = tk.Button(self,text="Create an Account",width=15,command=lambda: self.controller.show_frame(RegisterUser))
        self.btn_register.place(y=140, x=135, anchor=tk.NW, width=120)
        self.btn_login = tk.Button(self,text="Login", width=15, default="active", command=lambda: self.login())
        self.btn_login.place(y=140, x=265, anchor=tk.NW, width=100)
        self.bind("<<showframe>>", self.clear_contents)



    def login(self,*args):
    	#Establish Connection
        with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            #Find user If there is any take proper action
            find_user = ("SELECT * FROM users WHERE username = ? and password = ?")
            c.execute(find_user,[(self.txt_username.get()),(self.txt_password.get())])
            result = c.fetchone()
            if result:
                self.controller.welcome.set("Welcome " + result[1])
                self.controller.current_user["id"] = result[0]
                self.controller.current_user["username"] = result[1]
                self.controller.current_user["password"] = result[2]
                self.controller.current_user["birthday"] = result[3]
                self.controller.current_user["weight"] = result[4]
                self.controller.current_user["height"] = result[5]
                self.controller.current_user["calories"] = result[6]
                self.controller.current_user["protein"] = result[7]
                self.controller.current_user["carbs"] = result[8]
                self.controller.current_user["fat"] = result[9]
                self.controller.show_frame(MainScreen) #need that reference back to the controller object to access the show_frame method
            else:
                ms.showerror("Login!","Username and password are not correct.")



    def clear_contents(self,*args):
        #Clear the frames entry boxes and the current user object too
        self.txt_password.delete(0, tk.END) #clear the box - needed after deleting account
        self.txt_username.delete(0, tk.END) #clear the box - needed after deleting account
        self.controller.welcome.set("")
        self.controller.current_user["id"] = ""
        self.controller.current_user["username"] = ""
        self.controller.current_user["password"] = ""
        self.controller.current_user["birthday"] = ""
        self.controller.current_user["weight"] = ""
        self.controller.current_user["height"] = ""
        self.controller.current_user["calories"] = ""
        self.controller.current_user["protein"] = ""
        self.controller.current_user["carbs"] = ""
        self.controller.current_user["fat"] = ""



    def menubar(self, parent):
        #menubar code for this frame
        menubar = tk.Menu(parent)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)
        return menubar
        




class RegisterUser(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller #sets the controller to be referenced in the instance so you can use it again later
        self.bind("<Return>", self.register)
        self.focus_set()

        #setup variables linked to the comboboxes for easier updating
        self.day = tk.StringVar()
        self.month = tk.StringVar()
        self.year = tk.StringVar()

        #setup all the controls on this frame
        self.lbl_title = tk.Label(self, text="Create an Account", font=("Verdana", 14), bg="#9E7BB8", fg="white")
        self.lbl_title.place(y=0, x=0, width=500)
        self.lbl_name = tk.Label(self, width=10, anchor=tk.NE, text="Userame")
        self.lbl_name.place(y=50, x=85, width=100)
        self.lbl_password = tk.Label(self, width=10, anchor=tk.NE, text="Password")
        self.lbl_password.place(y=80, x=85, width=100)
        self.lbl_birthday = tk.Label(self, width=10, anchor=tk.NE, text="Birthday")
        self.lbl_birthday.place(y=110, x=85, width=100)
        self.lbl_weight = tk.Label(self, width=10, anchor=tk.NE, text="Weight(kg)")
        self.lbl_weight.place(y=140, x=85, width=100)
        self.lbl_height = tk.Label(self, width=10, anchor=tk.NE, text="Height(cm)")
        self.lbl_height.place(y=170, x=85, width=100)
        self.lbl_daily = tk.Label(self, width=10, anchor=tk.CENTER, text="Daily Macronutrient Goals", font=("Verdana", 12))
        self.lbl_daily.place(y=200, x=0, width=500)
        self.lbl_calories = tk.Label(self, width=10, anchor=tk.NE, text="Calories")
        self.lbl_calories.place(y=230, x=85, width=100)
        self.lbl_protein = tk.Label(self, width=10, anchor=tk.NE, text="Protein(g)-[4Cal/g]")
        self.lbl_protein.place(y=260, x=65, width=120)
        self.lbl_carbs = tk.Label(self, width=10, anchor=tk.NE, text="Carbohydrates(g)-[4Cal/g]")
        self.lbl_carbs.place(y=290, x=35, width=150)
        self.lbl_fat = tk.Label(self, width=10, anchor=tk.NE, text="Fat(g)-[9Cal/g]")
        self.lbl_fat.place(y=320, x=65, width=120)

        self.txt_username = tk.Entry(self, width=30)    
        self.txt_username.place(y=50, x=195, anchor=tk.NW, width=200)
        
        self.txt_password = tk.Entry(self, width=30, show="*")
        self.txt_password.place(y=80, x=195, anchor=tk.NW, width=200)
        
        self.cbo_day = ttk.Combobox(self, textvariable=self.day, state="readonly")
        self.cbo_day["values"] = self.controller.days
        self.cbo_day.current(0)
        self.cbo_day.place(y=110, x=195, anchor=tk.NW, width=40)
        self.cbo_day.bind("<<ComboboxSelected>>", lambda event:self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()))
        
        self.cbo_month = ttk.Combobox(self, textvariable=self.month, state="readonly")
        self.cbo_month["values"] = self.controller.months
        self.cbo_month.current(0)
        self.cbo_month.place(y=110, x=245, anchor=tk.NW, width=80)
        self.cbo_month.bind("<<ComboboxSelected>>", lambda event:self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()))
        
        self.cbo_year = ttk.Combobox(self, textvariable=self.year, state="readonly")
        self.cbo_year["values"] = self.controller.years
        self.cbo_year.current(0)
        self.cbo_year.place(y=110, x=335, anchor=tk.NW, width=60)
        self.cbo_year.bind("<<ComboboxSelected>>", lambda event:self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()))
        
        self.txt_weight = tk.Entry(self, width=30)
        self.txt_weight.place(y=140, x=195, anchor=tk.NW, width=40)
        self.txt_height = tk.Entry(self, width=30)    
        self.txt_height.place(y=170, x=195, anchor=tk.NW, width=40)
        self.txt_calories = tk.Entry(self, width=4)
        self.txt_calories.place(y=230, x=195, anchor=tk.NW, width=50)
        self.txt_protein = tk.Entry(self, width=3,)
        self.txt_protein.place(y=260, x=195, anchor=tk.NW, width=40)
        self.txt_carbs = tk.Entry(self, width=3,)
        self.txt_carbs.place(y=290, x=195, anchor=tk.NW, width=40)
        self.txt_fat = tk.Entry(self, width=3)
        self.txt_fat.place(y=320, x=195, anchor=tk.NW, width=40)

        self.btn_register = tk.Button(self,text="Cancel",width=15,command=lambda: controller.show_frame(LoginPage))
        self.btn_register.place(y=350, x=145, anchor=tk.NW, width=100)
        self.btn_login = tk.Button(self,text="Create Account", width=15, default="active", command=lambda: self.register())
        self.btn_login.place(y=350, x=255, anchor=tk.NW, width=100)
        self.bind("<<showframe>>", self.load_default_values)



    def load_default_values(self,*args):
        #loads the current user info from the controller Dict into the page
        self.txt_username.delete(0, tk.END) 
        self.txt_password.delete(0, tk.END)
        self.cbo_day.set(str(datetime.now().day).zfill(2))        
        self.cbo_month.set(list(self.controller.month_mapping.keys())[list(self.controller.month_mapping.values()).index(str(datetime.now().month).zfill(2))])
        self.cbo_year.set(str(datetime.now().year).zfill(2))
        self.txt_weight.delete(0, tk.END)
        self.txt_height.delete(0, tk.END)
        self.txt_calories.delete(0, tk.END)
        self.txt_calories.insert(0,"1994")
        self.txt_protein.delete(0, tk.END)
        self.txt_protein.insert(0,"145")
        self.txt_carbs.delete(0, tk.END)
        self.txt_carbs.insert(0,"205")
        self.txt_fat.delete(0, tk.END)
        self.txt_fat.insert(0,"66")


    def register(self,*args):
        #INSERTing the new user data into the database and some validation beforehand
        if self.txt_username.get() == "":
            ms.showwarning("Warning","Username cannot be blank")
            return
        if self.txt_password.get() == "":
            ms.showwarning("Warning","Password cannot be blank")
            return
        if self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()) == False:
            return
        if self.txt_weight.get() == "":
            ms.showwarning("Warning","Weight cannot be blank")
            return
        if self.txt_height.get() == "":
            ms.showwarning("Warning","Height cannot be blank")
            return
        if self.txt_calories.get() == "":
            ms.showwarning("Warning","Calories cannot be blank")
            return
        if self.txt_protein.get() == "":
            ms.showwarning("Warning","Protein cannot be blank")
            return
        if self.txt_carbs.get() == "":
            ms.showwarning("Warning","Carbohydrates cannot be blank")
            return
        if self.txt_fat.get() == "":
            ms.showwarning("Warning","Fat cannot be blank")
            return
        
        if self.controller.insert_new_user(self, self.txt_username.get(), self.txt_password.get(), self.day.get()+"-"+self.controller.month_mapping[self.month.get()]+"-"+self.year.get(), self.txt_weight.get(), self.txt_height.get(), self.txt_calories.get(), self.txt_protein.get(), self.txt_carbs.get(), self.txt_fat.get()):
            self.controller.show_frame(LoginPage) #need that reference back to the controller object to access the show_frame method



    def menubar(self, parent):
        menubar = tk.Menu(parent)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)
        return menubar



    

class EditProfile(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller #sets the controller to be referenced in the instance so you can use it again later
        self.bind("<Return>", self.register)
        self.focus_set()

        self.day = tk.StringVar()
        self.month = tk.StringVar()
        self.year = tk.StringVar()

        #setup all the controls on this frame
        self.lbl_title = tk.Label(self, text="Edit Your Account", font=("Verdana", 14), bg="#9E7BB8", fg="white")
        self.lbl_title.place(y=0, x=0, width=500)
        self.lbl_name = tk.Label(self, width=10, anchor=tk.NE, text="Userame")
        self.lbl_name.place(y=50, x=85, width=100)
        self.lbl_password = tk.Label(self, width=10, anchor=tk.NE, text="Password")
        self.lbl_password.place(y=80, x=85, width=100)
        self.lbl_birthday = tk.Label(self, width=10, anchor=tk.NE, text="Date of Birth")
        self.lbl_birthday.place(y=110, x=85, width=100)
        self.lbl_weight = tk.Label(self, width=10, anchor=tk.NE, text="Weight(kg)")
        self.lbl_weight.place(y=140, x=85, width=100)
        self.lbl_height = tk.Label(self, width=10, anchor=tk.NE, text="Height(cm)")
        self.lbl_height.place(y=170, x=85, width=100)
        self.lbl_daily = tk.Label(self, width=10, anchor=tk.CENTER, text="Daily Macronutrient Goals", font=("Verdana", 12))
        self.lbl_daily.place(y=200, x=0, width=500)
        self.lbl_calories = tk.Label(self, width=10, anchor=tk.NE, text="Calories")
        self.lbl_calories.place(y=230, x=85, width=100)
        self.lbl_protein = tk.Label(self, width=10, anchor=tk.NE, text="Protein(g)-[4Cal/g]")
        self.lbl_protein.place(y=260, x=65, width=120)
        self.lbl_carbs = tk.Label(self, width=10, anchor=tk.NE, text="Carbohydrates(g)-[4Cal/g]")
        self.lbl_carbs.place(y=290, x=35, width=150)
        self.lbl_fat = tk.Label(self, width=10, anchor=tk.NE, text="Fat(g)-[9Cal/g]")
        self.lbl_fat.place(y=320, x=65, width=120)

        self.txt_username = tk.Entry(self, width=30)    
        self.txt_username.place(y=50, x=195, anchor=tk.NW, width=200)
        
        self.txt_password = tk.Entry(self, width=30, show="*")
        self.txt_password.place(y=80, x=195, anchor=tk.NW, width=200)
        
        self.cbo_day = ttk.Combobox(self, textvariable=self.day, state="readonly")
        self.cbo_day["values"] = self.controller.days
        self.cbo_day.current(0)
        self.cbo_day.place(y=110, x=195, anchor=tk.NW, width=40)
        self.cbo_day.bind("<<ComboboxSelected>>", lambda event:self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()))
        
        self.cbo_month = ttk.Combobox(self, textvariable=self.month, state="readonly")
        self.cbo_month["values"] = self.controller.months
        self.cbo_month.current(0)
        self.cbo_month.place(y=110, x=245, anchor=tk.NW, width=80)
        self.cbo_month.bind("<<ComboboxSelected>>", lambda event:self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()))
        
        self.cbo_year = ttk.Combobox(self, textvariable=self.year, state="readonly")
        self.cbo_year["values"] = self.controller.years
        self.cbo_year.current(0)
        self.cbo_year.place(y=110, x=335, anchor=tk.NW, width=60)
        self.cbo_year.bind("<<ComboboxSelected>>", lambda event:self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()))
        
        self.txt_weight = tk.Entry(self, width=30)
        self.txt_weight.place(y=140, x=195, anchor=tk.NW, width=40)
        self.txt_height = tk.Entry(self, width=30)    
        self.txt_height.place(y=170, x=195, anchor=tk.NW, width=40)
        self.txt_calories = tk.Entry(self, width=4)
        self.txt_calories.place(y=230, x=195, anchor=tk.NW, width=50)
        self.txt_protein = tk.Entry(self, width=3,)
        self.txt_protein.place(y=260, x=195, anchor=tk.NW, width=40)
        self.txt_carbs = tk.Entry(self, width=3,)
        self.txt_carbs.place(y=290, x=195, anchor=tk.NW, width=40)
        self.txt_fat = tk.Entry(self, width=3)
        self.txt_fat.place(y=320, x=195, anchor=tk.NW, width=40)

        self.btn_register = tk.Button(self,text="Cancel",width=15,command=lambda: self.controller.show_frame(MainScreen))
        self.btn_register.place(y=350, x=145, anchor=tk.NW, width=100)
        self.btn_login = tk.Button(self,text="Commit Changes", width=15, default="active", command=lambda: self.update_profile())
        self.btn_login.place(y=350, x=255, anchor=tk.NW, width=100)

        #setup update event for the frame - runs when switching to the frame 
        self.bind("<<showframe>>", self.load_current_user)



    def load_current_user(self,*args):
        #loads the current user info from the controller Dict into the page
        self.txt_username.delete(0, tk.END) 
        self.txt_username.insert(0, self.controller.current_user["username"])
        self.txt_password.delete(0, tk.END)
        self.txt_password.insert(0, self.controller.current_user["password"])
        self.birthday = self.controller.current_user["birthday"].split("-")
        self.cbo_day.set(self.birthday[0])        
        self.cbo_month.set(list(self.controller.month_mapping.keys())[list(self.controller.month_mapping.values()).index(self.birthday[1])])
        self.cbo_year.set(self.birthday[2])
        self.txt_weight.delete(0, tk.END)
        self.txt_weight.insert(0,self.controller.current_user["weight"])
        self.txt_height.delete(0, tk.END)
        self.txt_height.insert(0,self.controller.current_user["height"])
        self.txt_calories.delete(0, tk.END)
        self.txt_calories.insert(0,self.controller.current_user["calories"])
        self.txt_protein.delete(0, tk.END)
        self.txt_protein.insert(0,self.controller.current_user["protein"])
        self.txt_carbs.delete(0, tk.END)
        self.txt_carbs.insert(0,self.controller.current_user["carbs"])
        self.txt_fat.delete(0, tk.END)
        self.txt_fat.insert(0,self.controller.current_user["fat"])




    def update_profile(self,*args):
        #update the edited account data to the database
        if self.txt_username.get() == "":
            ms.showwarning("Warning","Username cannot be blank")
            return
        if self.txt_password.get() == "":
            ms.showwarning("Warning","Password cannot be blank")
            return
        if self.controller.check_date(self.controller,self.day.get(),self.month.get(),self.year.get()) == False:
            return
        if self.txt_weight.get() == "":
            ms.showwarning("Warning","Weight cannot be blank")
            return
        if self.txt_height.get() == "":
            ms.showwarning("Warning","Height cannot be blank")
            return
        if self.txt_calories.get() == "":
            ms.showwarning("Warning","Calories cannot be blank")
            return
        if self.txt_protein.get() == "":
            ms.showwarning("Warning","Protein cannot be blank")
            return
        if self.txt_carbs.get() == "":
            ms.showwarning("Warning","Carbohydrates cannot be blank")
            return
        if self.txt_fat.get() == "":
            ms.showwarning("Warning","Fat cannot be blank")
            return
    	#Establish Connection
        if self.controller.update_current_user(self, self.txt_username.get(), self.txt_password.get(), self.day.get()+"-"+self.controller.month_mapping[self.month.get()]+"-"+self.year.get(), self.txt_weight.get(), self.txt_height.get(), self.txt_calories.get(), self.txt_protein.get(), self.txt_carbs.get(), self.txt_fat.get()):
            #if update was successful, update the controller CurrentUser Dict with the updated values
            self.controller.welcome.set("Welcome " + self.txt_username.get())
            self.controller.current_user["username"] = self.txt_username.get()
            self.controller.current_user["password"] = self.txt_password.get()
            self.controller.current_user["birthday"] = self.day.get()+"-"+self.controller.month_mapping[self.month.get()]+"-"+self.year.get()
            self.controller.current_user["height"] = self.txt_height.get()
            self.controller.current_user["weight"] = self.txt_weight.get()
            self.controller.current_user["calories"] = self.txt_calories.get()
            self.controller.current_user["protein"] = self.txt_protein.get()
            self.controller.current_user["carbs"] = self.txt_carbs.get()
            self.controller.current_user["fat"] = self.txt_fat.get()
            self.controller.show_frame(MainScreen) #need that reference back to the controller object to access the show_frame method
            



    def menubar(self, parent):
        menubar = tk.Menu(parent)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_command(label="Home", command=lambda: self.controller.show_frame(MainScreen))
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="Log Out", command=lambda: self.controller.show_frame(LoginPage))
        account_menu.add_command(label="Edit Account", command=lambda: self.controller.show_frame(EditProfile))
        account_menu.add_command(label="Delete Account", command=lambda: self.controller.delete_record_from_table(self.controller, "users", self.controller.current_user["id"], "Permanently Delete Account?", "You are about to permanently delete your account, are you sure you wish to do this?",LoginPage))
        menubar.add_cascade(label="Account", menu=account_menu)
        menubar.add_command(label="Food Diary", command=lambda: self.controller.show_frame(FoodDiary))
        return menubar




class FoodDiary(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller #sets the controller to be referenced in the instance so you can use it again later
        self.bind("<Return>", lambda: self.register)
        self.focus_set()
        self.lbl_title = tk.Label(self, text="Food Diary", font=("Verdana", 14), bg="#9E7BB8", fg="white")
        self.lbl_title.place(y=0, x=0, width=500)
        
        self.day = tk.StringVar()
        self.month = tk.StringVar()
        self.year = tk.StringVar()

        #setup controls for this frame
        self.lbl_showing = tk.Label(self, text="Showing Diary Entries for: ")
        self.lbl_showing.place(y=40, x=60, width=150)

        self.cbo_day = ttk.Combobox(self, textvariable=self.day, state="readonly")
        self.cbo_day["values"] = self.controller.days
        self.cbo_day.current(0)
        self.cbo_day.place(y=40, x=220, anchor=tk.NW, width=40)
        self.cbo_day.bind("<<ComboboxSelected>>",  lambda event:self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get()))
        
        self.cbo_month = ttk.Combobox(self, textvariable=self.month, state="readonly")
        self.cbo_month["values"] = self.controller.months
        self.cbo_month.current(0)
        self.cbo_month.place(y=40, x=270, anchor=tk.NW, width=80)
        self.cbo_month.bind("<<ComboboxSelected>>",  lambda event:self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get()))
        
        self.cbo_year = ttk.Combobox(self, textvariable=self.year, state="readonly")
        self.cbo_year["values"] = self.controller.years
        self.cbo_year.current(0)
        self.cbo_year.place(y=40, x=360, anchor=tk.NW, width=60)
        self.cbo_year.bind("<<ComboboxSelected>>",  lambda event:self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get()))

        #Treeview object setup to match record
        self.tree= ttk.Treeview(self, column=("id", "food_name", "food_weight", "calories", "protein", "carbs", "fat"), selectmode="browse", show="headings")
        self.tree.heading("id", text="id")
        self.tree.column("id", minwidth=0, width=0, stretch=tk.NO)
        self.tree.heading("food_name", text="Food")
        self.tree.column("food_name", minwidth=93, width=93, stretch=tk.NO)
        self.tree.heading("food_weight", text="Weight")
        self.tree.column("food_weight", minwidth=75, width=75, stretch=tk.NO)
        self.tree.heading("calories", text="Calories")
        self.tree.column("calories", minwidth=75, width=75, stretch=tk.NO)
        self.tree.heading("protein", text="Protein")
        self.tree.column("protein", minwidth=75, width=75, stretch=tk.NO)
        self.tree.heading("carbs", text="Carbs")
        self.tree.column("carbs", minwidth=75, width=75, stretch=tk.NO)
        self.tree.heading("fat", text="Fat")
        self.tree.column("fat", minwidth=75, width=75, stretch=tk.NO)
        self.tree.place(x=7, y=70, width=485, height=200)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.place(x=474, y=71, height=198)

        self.lbl_food = tk.Label(self, width=10, anchor=tk.NE, text="Food Name")
        self.lbl_food.place(y=290, x=-200, width=80)
        self.txt_food = tk.Entry(self, width=30)
        self.txt_food.place(y=290, x=-200, anchor=tk.NW, width=80)        
        self.lbl_weight = tk.Label(self, width=10, anchor=tk.NE, text="Weight")
        self.lbl_weight.place(y=320, x=-200, width=80)
        self.txt_weight = tk.Entry(self, width=30)
        self.txt_weight.place(y=320, x=-200, anchor=tk.NW, width=80)
        self.lbl_calories = tk.Label(self, width=10, anchor=tk.NE, text="Calories")
        self.lbl_calories.place(y=350, x=-200, width=80)
        self.txt_calories = tk.Entry(self, width=30)
        self.txt_calories.place(y=350, x=-200, anchor=tk.NW, width=80)
        self.lbl_protein = tk.Label(self, width=10, anchor=tk.NE, text="Protein")
        self.lbl_protein.place(y=290, x=-200, width=80)
        self.txt_protein = tk.Entry(self, width=30)
        self.txt_protein.place(y=290, x=-200, anchor=tk.NW, width=80)
        self.lbl_carbs = tk.Label(self, width=10, anchor=tk.NE, text="Carbohydrates")
        self.lbl_carbs.place(y=320, x=-200, width=80)
        self.txt_carbs = tk.Entry(self, width=30)
        self.txt_carbs.place(y=320, x=-200, anchor=tk.NW, width=80)
        self.lbl_fat = tk.Label(self, width=10, anchor=tk.NE, text="fat")
        self.lbl_fat.place(y=350, x=-200, width=80)
        self.txt_fat = tk.Entry(self, width=30)
        self.txt_fat.place(y=350, x=-200, anchor=tk.NW, width=80)

        self.lbl_click = tk.Label(self, width=10, anchor=tk.CENTER, text="Click an item in the list above to edit it")
        self.lbl_click.place(y=280, x=10, anchor=tk.NW, width=240)

        self.btn_update = tk.Button(self, text="Update this Food", width=15, command=lambda: self.update_food(self))
        self.btn_update.place(y=-1000, x=130, anchor=tk.NW, width=115)
        self.btn_delete = tk.Button(self, text="Delete this Food", width=15,command=lambda: self.delete_food(self))
        self.btn_delete.place(y=-1000, x=255, anchor=tk.NW, width=115)
        self.btn_save = tk.Button(self, text="Save the above as a new Food", width=15,command=lambda: self.save_food(self))
        self.btn_save.place(y=-1000, x=130, anchor=tk.NW, width=230)
        self.btn_insert = tk.Button(self, text="Add a new Food", width=15,command=lambda: self.show_insert_frame(self))
        self.btn_insert.place(y=280, x=255, anchor=tk.NW, width=115)
        self.btn_export = tk.Button(self, text="Backup Diary", width=15, default="active", command=lambda: self.controller.export_food_diary(self.controller))
        self.btn_export.place(y=280, x=380, anchor=tk.NW, width=115)

        #setup update event for the treeview - runs when treeview selection is
        self.tree.bind("<<TreeviewSelect>>", self.update_entries)
        #setup update event for the frame - runs when switching to the frame 
        self.bind("<<showframe>>", self.show_update_frame)

        

    def clear_entries(self, *args):        
        self.txt_food.delete(0, tk.END)
        self.txt_weight.delete(0, tk.END)
        self.txt_calories.delete(0, tk.END)
        self.txt_protein.delete(0, tk.END)
        self.txt_carbs.delete(0, tk.END)
        self.txt_fat.delete(0, tk.END)



    def update_entries(self, *args):
        self.clear_entries(self)
        self.hide_show_controls(self, "show_update")
        self.txt_food.insert(0, self.tree.item(self.tree.selection())["values"][1])
        self.txt_weight.insert(0, self.tree.item(self.tree.selection())["values"][2])
        self.txt_calories.insert(0, self.tree.item(self.tree.selection())["values"][3])
        self.txt_protein.insert(0, self.tree.item(self.tree.selection())["values"][4])
        self.txt_carbs.insert(0, self.tree.item(self.tree.selection())["values"][5])
        self.txt_fat.insert(0, self.tree.item(self.tree.selection())["values"][6])



    @staticmethod     
    def hide_show_controls(self, action):
        #Hides and shows the controls for updates and deletes so they only appear when something is selected
        if action == "hide_update" or action == "hide_insert":
            #if a "hide" action, hide everything
            self.lbl_food.place(y=330, x=-200, width=80)
            self.txt_food.place(y=330, x=-200, anchor=tk.NW, width=80)        
            self.lbl_weight.place(y=350, x=-200, width=80)
            self.txt_weight.place(y=350, x=-200, anchor=tk.NW, width=80)
            self.lbl_calories.place(y=390, x=-200, width=80)
            self.txt_calories.place(y=390, x=-200, anchor=tk.NW, width=80)
            self.lbl_protein.place(y=330, x=-200, width=80)
            self.txt_protein.place(y=330, x=-200, anchor=tk.NW, width=80)
            self.lbl_carbs.place(y=350, x=-200, width=80)
            self.txt_carbs.place(y=350, x=-200, anchor=tk.NW, width=80)
            self.lbl_fat.place(y=390, x=-200, width=80)
            self.txt_fat.place(y=390, x=-200, anchor=tk.NW, width=80)
            self.btn_update.place(y=-1000, x=130, anchor=tk.NW, width=115)
            self.btn_delete.place(y=-1000, x=255, anchor=tk.NW, width=115)
            self.btn_save.place(y=-1000, x=255, anchor=tk.NW, width=230)
        else:
            #if a "show" action show the labels and textboxes
            self.lbl_food.place(y=330, x=25, width=80)
            self.txt_food.place(y=330, x=115, anchor=tk.NW, width=80)        
            self.lbl_weight.place(y=360, x=25, width=80)
            self.txt_weight.place(y=360, x=115, anchor=tk.NW, width=80)
            self.lbl_calories.place(y=390, x=25, width=80)
            self.txt_calories.place(y=390, x=115, anchor=tk.NW, width=80)
            self.lbl_protein.place(y=330, x=235, width=80)
            self.txt_protein.place(y=330, x=325, anchor=tk.NW, width=80)
            self.lbl_carbs.place(y=360, x=235, width=80)
            self.txt_carbs.place(y=360, x=325, anchor=tk.NW, width=80)
            self.lbl_fat.place(y=390, x=235, width=80)
            self.txt_fat.place(y=390, x=325, anchor=tk.NW, width=80)
        #handle the cuttons for the "show" action   
        if action == "show_update":
            #show the update/delete buttons, hide the save button
            self.btn_update.place(y=420, x=130, anchor=tk.NW, width=115)
            self.btn_delete.place(y=420, x=255, anchor=tk.NW, width=115)
            self.btn_save.place(y=-1000, x=255, anchor=tk.NW, width=230)
        elif action == "show_insert":
            #Show the save button, hide the update/delete buttons
            self.btn_save.place(y=420, x=130, anchor=tk.NW, width=230)
            self.btn_update.place(y=-1000, x=130, anchor=tk.NW, width=115)
            self.btn_delete.place(y=-1000, x=255, anchor=tk.NW, width=115)


        
    @staticmethod   
    def update_frame_controls(self,param_day,param_month,param_year):
        #updates the tree with data from the database whenever the date changes
        self.clear_entries(self)
        self.hide_show_controls(self, "hide_update")
        self.controller.check_date(self.controller,param_day,param_month,param_year)
        self.tree.delete(*self.tree.get_children())
        with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            sqlstring = """SELECT id, food_name, food_weight, calories, protein, carbs, fat FROM food_diary WHERE `date` = ? AND `user_id` = ? ORDER BY `food_name` ASC"""
            populate_tree = (sqlstring)
            c.execute(populate_tree,[(param_day+"-"+self.controller.month_mapping[param_month]+"-"+param_year), self.controller.current_user["id"]])
            rows = c.fetchall()
            for row in rows:
                self.tree.insert("", tk.END, values=row)


    def delete_food(self,*args):
        #execute the delete query for food and updates screen
        self.controller.delete_record_from_table(self.controller, "food_diary", self.tree.item(self.tree.selection())["values"][0], "Permanently Delete Food?", "You are about to permanently delete this Food, are you sure you wish to do this?")
        self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get())



    def update_food(self,*args):
        #execute the update query for food and updates screen
        self.controller.update_existing_food(self, self.txt_food.get(), self.txt_weight.get(), self.txt_calories.get(), self.txt_protein.get(), self.txt_carbs.get(), self.txt_fat.get(), self.tree.item(self.tree.selection())["values"][0])
        self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get())



    def save_food(self,*args):
        #execute the insert query for food and updates screen
        self.controller.insert_new_food(self, self.txt_food.get(), self.txt_weight.get(), self.txt_calories.get(), self.txt_protein.get(), self.txt_carbs.get(), self.txt_fat.get())
        self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get())



    def show_insert_frame(self, *args):
        #when the treeview is clicked, this function populates and shows the "Insert" part of the screen allowing the user to add a new food item
        self.clear_entries(self)
        self.hide_show_controls(self, "show_insert")


                
    def show_update_frame(self, *args):
        #when the treeview is clicked, this function populates and shows the "update" part of the screen allowing the user to edit or delete the item they clicked
        self.clear_entries(self)
        self.hide_show_controls(self, "show_update")
        #Just need to set the date to today when the frame updates, everything else is done by the combobox updates
        self.cbo_month.set(list(self.controller.month_mapping.keys())[list(self.controller.month_mapping.values()).index(str(datetime.now().month).zfill(2))])
        self.cbo_day.set(str(datetime.now().day).zfill(2))        
        self.cbo_year.set(datetime.now().year)
        self.update_frame_controls(self,self.day.get(),self.month.get(),self.year.get())


        
    def menubar(self, parent):
        menubar = tk.Menu(parent)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_command(label="Home", command=lambda: self.controller.show_frame(MainScreen))
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="Log Out", command=lambda: self.controller.show_frame(LoginPage))
        account_menu.add_command(label="Edit Account", command=lambda: self.controller.show_frame(EditProfile))
        account_menu.add_command(label="Delete Account", command=lambda: self.controller.delete_record_from_table(self.controller, "users", self.controller.current_user["id"], "Permanently Delete Account?", "You are about to permanently delete your account, are you sure you wish to do this?",LoginPage))
        menubar.add_cascade(label="Account", menu=account_menu)
        menubar.add_command(label="Food Diary", command=lambda: self.controller.show_frame(FoodDiary))
        return menubar





class MainScreen(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller #sets the controller to be referenced in the instance so you can use it again later
        self.bind("<Return>", self.register)
        self.focus_set()

        self.var_calories_used = tk.StringVar()
        self.var_protein_used = tk.StringVar()
        self.var_carbs_used = tk.StringVar()
        self.var_fat_used = tk.StringVar()

        #setup controls for this frame
        self.lbl_title = tk.Label(self, textvariable=self.controller.welcome, font=("Verdana", 14), bg="#9E7BB8", fg="white")
        self.lbl_title.place(y=0, x=0, width=500)

        self.lbl_daily = tk.Label(self, width=10, anchor=tk.CENTER, text="Daily Macronutrient Goals", font=("Verdana", 12)).place(y=40, x=0, width=500)
        
        self.lbl_calories_used = tk.Label(self, width=10, anchor=tk.E, text="", textvariable=self.var_calories_used, font=("Verdana", 12), fg="green")
        self.lbl_calories_used.place(y=68, x=100, width=100)
        self.lbl_protein_used = tk.Label(self, width=10, anchor=tk.E, text="", textvariable=self.var_protein_used, font=("Verdana", 12), fg="green")
        self.lbl_protein_used.place(y=98, x=100, width=100)
        self.lbl_carbs_used = tk.Label(self, width=10, anchor=tk.E, text="", textvariable=self.var_carbs_used, font=("Verdana", 12), fg="green")
        self.lbl_carbs_used.place(y=128, x=100, width=100)
        self.lbl_fat_used = tk.Label(self, width=10, anchor=tk.E, text="", textvariable=self.var_fat_used, font=("Verdana", 12), fg="green")
        self.lbl_fat_used.place(y=158, x=100, width=100)

        self.lbl_calories = tk.Label(self, width=10, anchor=tk.W, text="Calories Remaining")
        self.lbl_calories.place(y=70, x=200, width=250)
        self.lbl_protein = tk.Label(self, width=10, anchor=tk.W, text="(g) Protein Remaining")
        self.lbl_protein.place(y=100, x=200, width=250)
        self.lbl_carbs = tk.Label(self, width=10, anchor=tk.W, text="(g) Carbohydrates Remaining")
        self.lbl_carbs.place(y=130, x=200, width=250)
        self.lbl_fat = tk.Label(self, width=10, anchor=tk.W, text="(g) Fat Remaining")
        self.lbl_fat.place(y=160, x=200, width=250)

        #setup update event for the frame - runs when switching to the frame 
        self.bind("<<showframe>>", self.update_goals)



    def update_goals(self,*args):
        #update the totals on the home page
        #default to green text
        self.lbl_calories_used.config(fg="green")
        self.lbl_protein_used.config(fg="green")
        self.lbl_carbs_used.config(fg="green")
        self.lbl_fat_used.config(fg="green")
        int_calories_used = 0
        int_protein_used = 0
        int_carbs_used = 0
        int_fat_used = 0
        with sqlite3.connect("python_nutrition.db") as db:
            c = db.cursor()
            sqlstring = """SELECT sum(calories) as t_calories, sum(protein) as t_protein, sum(carbs) as t_carbs, sum(fat) as t_fat FROM food_diary WHERE `user_id` = ?  and date = ? ORDER BY `date`, `food_name` ASC"""
            update_goal_query = (sqlstring)
            c.execute(update_goal_query,[self.controller.current_user["id"],(str(datetime.now().day).zfill(2) +"-"+ str(datetime.now().month).zfill(2) +"-"+ str(datetime.now().year))])
            result = c.fetchone()
            rowcount = c.rowcount
            if result:
                if result[0] is not None:
                    calc_val = math.ceil(float(self.controller.current_user["calories"]) - float(result[0]))
                    self.var_calories_used.set(calc_val)
                    int_calories_used = int(float(result[0])) #set to total cals (from database)
                    if calc_val < 0:
                        self.lbl_calories_used.config(fg="red")  #set color to red as it's a negative number
                else :
                    self.var_calories_used.set(self.controller.current_user["calories"]) #set to current limit
                    
                if result[1] is not None:
                    calc_val = math.ceil(float(self.controller.current_user["protein"]) - float(result[1]))
                    self.var_protein_used.set(calc_val)
                    int_protein_used = int(float(result[1])) #set to total protein (from database)
                    if calc_val < 0:
                        self.lbl_protein_used.config(fg="red")  #set color to red as it's a negative number
                else :
                    self.var_protein_used.set(self.controller.current_user["protein"]) #set to current limit
                    
                if result[2] is not None:
                    calc_val = math.ceil(float(self.controller.current_user["carbs"]) - float(result[2]))
                    self.var_carbs_used.set(calc_val)
                    int_carbs_used = int(float(result[2])) #set to total carbs (from database)
                    if calc_val < 0:
                        self.lbl_carbs_used.config(fg="red")  #set color to red as it's a negative number
                else :
                    self.var_carbs_used.set(self.controller.current_user["carbs"]) #set to current limit

                    
                if result[3] is not None:
                    calc_val = math.ceil(float(self.controller.current_user["fat"]) - float(result[3]))
                    self.var_fat_used.set(calc_val)
                    int_fat_used = int(float(result[3])) #set to total fat (from database)
                    if calc_val < 0:
                        self.lbl_fat_used.config(fg="red")  #set color to red as it's a negative number
                else :
                    self.var_fat_used.set(self.controller.current_user["fat"]) #set to current limit

            else:
                self.var_calories_used.set(self.controller.current_user["calories"])
                self.var_protein_used.set(self.controller.current_user["protein"])
                self.var_carbs_used.set(self.controller.current_user["carbs"])
                self.var_fat_used.set(self.controller.current_user["fat"])

        fig_macros = Figure(figsize=(4,4), dpi=100)
        fig_macros.patch.set_facecolor("#f0f0f0")
        subplot = fig_macros.add_subplot(111)

        #conversion for the graph
        int_calories = int(float(self.controller.current_user["calories"]))
        int_protein = int(float(self.controller.current_user["protein"]))
        int_carbs = int(float(self.controller.current_user["carbs"]))
        int_fat = int(float(self.controller.current_user["fat"]))

        #cals are 1000s while fats are <100 - I divided cals by 10 to make them similar numbers, the ratio is the same
        macros_used = (int_calories_used/10, int_protein_used, int_carbs_used, int_fat_used)#plots for the total macro used that day
        macros_unused = ((int_calories-int_calories_used)/10, int_protein - int_protein_used, int_carbs - int_fat_used, int_fat-int_fat_used)#plots for the total daily macro values

        ind = numpy.arange(4)  # the x locations for the groups
        width = .5

        macros_used_bar = subplot.bar(ind, macros_used, width)#blue bars are the total  macros used
        macros_unused_bar = subplot.bar(ind, macros_unused, width, bottom=macros_used)#orange bars are the total daily value minus the total macros used

        subplot.set_xticks([0, 1, 2, 3]) #x-axis labels for the bard
        subplot.set_xticklabels(['Calories', 'Protein', 'Carbs', 'Fat'])
        subplot.set_yticks([])
        subplot.set_yticklabels([])
        subplot.legend((macros_used_bar[0], macros_unused_bar[0]), ('current', 'goal'))

        self.canvas = FigureCanvasTkAgg(fig_macros, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().place(y=200, x=0, width=500, height=255)

    def menubar(self, parent):
        menubar = tk.Menu(parent)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_command(label="Home", command=lambda: self.controller.show_frame(MainScreen))
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="Log Out", command=lambda: self.controller.show_frame(LoginPage))
        account_menu.add_command(label="Edit Account", command=lambda: self.controller.show_frame(EditProfile))
        account_menu.add_command(label="Delete Account", command=lambda: self.controller.delete_record_from_table(self.controller, "users", self.controller.current_user["id"], "Permanently Delete Account?", "You are about to permanently delete your account, are you sure you wish to do this?",LoginPage))
        menubar.add_cascade(label="Account", menu=account_menu)
        menubar.add_command(label="Food Diary", command=lambda: self.controller.show_frame(FoodDiary))
        return menubar
    


        


app = pyNutrition()
app.mainloop()
