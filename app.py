import hashlib, math, datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from money import *
from pymongo.mongo_client import MongoClient
import pandas as pd
from forex_python.converter import CurrencyCodes
from io import BytesIO

uri = "mongodb+srv://noanh07:5Pn3wmjC3IIcME7y@expense-tracker.0wqemg6.mongodb.net/?retryWrites=true&w=majority&appName=Expense-Tracker"
client = MongoClient(uri)
database = client["Expense-Tracker"]

app = Flask(__name__)

app.secret_key = 'defcb16b51fb5722a887a9a904855a57d7eeb584afcaf012'

def hash_string(input_string):
    sha256 = hashlib.sha256()
    input_bytes = input_string.encode('utf-8')
    sha256.update(input_bytes)
    hashed_string = sha256.hexdigest()
    return hashed_string


def returnSymbol(value):
    c = CurrencyCodes()
    return c.get_symbol(value)


app.jinja_env.filters["symbol"] = returnSymbol


def currencyBefore(value):
    if 'user_id' in session:
        user = database.user.find_one({"id": session["user_id"]})
        if user:
            res = db.settings.find_one({"token": user["token"]})
            if res:
                isBefore = res.get("isCurrencyBefore")
                currency = res.get("currency")
                if isBefore:
                    return f"{currency}{round(value, 2):,}"
                else:
                    return f"{round(value, 2):,}{currency}"


app.jinja_env.filters["comma"] = currencyBefore


@app.context_processor
def inject_global():
    if 'user_id' in session:
        user = database.user.find_one({"id": session["user_id"]})
        if user:
            res = db.settings.find_one({"token": user["token"]})
            if res:
                return dict(version=getVersion(), currency=res.get("currency"))

    return dict(version=getVersion(), currency="€")


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = database.user.find_one({"username": username, "password": hash_string(password)})
        if user:
            session['user_id'] = user["id"]
            database.user.update_one({"token": user["token"]}, {"$set": {"lastConnexion": datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}})
            return redirect(url_for('home'))
        else:
            return redirect(url_for("login", code = 9))

    return render_template('login.html')


@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    code = request.args.get('code', default = None, type = int)
    budget = updateBudget(user["token"])
    labels, amount, color, bcolor = updateChart(user["token"])
    date, amounts = updateCourbe(user["token"])
    totalLabel, totals = summary(user["token"])

    res = db.settings.find_one({"token": user["token"]})
    if "color" in res:
        gcolor = f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 0.7)"
        gbcolor = f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 1)"
    else:
        gcolor = "blue"
        gbcolor = "blue"

    return render_template("index.html", user = user, budget = budget, totalLabel = totalLabel, totals = totals, labels = labels, values = amount, color = color, bcolor = bcolor, date = date, amounts = amounts, gcolor = gcolor, gbcolor = gbcolor)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        confirmpassword = request.form['confirmpassword']
        if password == confirmpassword:
            userr = database.user.find_one({"username": username})
            if not userr:
                mail = database.user.find_one({"email": email})
                if mail is None:
                    tkn = generateToken(25, random.randint(25, 50))
                    i = database.user.find_one({}, sort = [("id", -1)])
                    if i is not None:
                        database.user.insert_one({"id": i["id"] + 1, "username": username, "password": hash_string(password), "token": tkn, "budget": 0, "lastConnexion": datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'), "creationDate": datetime.datetime.now().timestamp(), "email": email})
                    else:
                        database.user.insert_one({"id": 0, "username": username, "password": hash_string(password), "token": tkn, "budget": 0, "lastConnexion": datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'), "creationDate": datetime.datetime.now().timestamp(), "email": email})
                    i = database.category.find_one({}, sort = [("id", -1)])
                    if i is not None:
                        database.category.insert_one({"id": i["id"] + 1, "token": tkn, "name": "Eco", "color": "#ad3434"})
                    else:
                        database.category.insert_one({"id": 0, "token": tkn, "name": "Eco", "color": "#ad3434"})
                    database.settings.insert_one({"token": tkn, "currency": "€"})
                    return redirect(url_for('login', code = 10))
                else:
                    return redirect(url_for('register', code = 13))
            else:
                return redirect(url_for('register', code = 11))
        else:
            return redirect(url_for('register', code = 12))

    return render_template('register.html')


@app.route("/manage", methods = ["GET", "POST"])
def manage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    values = []
    if request.method == "POST":
        for key in request.form:
            values.append(request.form.getlist(key))
        addCategory(user["token"], values[0], values[1])
        return redirect(url_for("home", code = 4))
    else:
        return render_template("manage.html")


@app.route("/categories", methods = ["GET", "POST"])
def categories():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    categories = getCategory(user["token"])

    return render_template("categories.html", liste = categories)


@app.route("/editcategory", methods = ["GET", "POST"])
def editCat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "Supprimer":
            deleteCategory(request.form.get("id"), user["token"])
            return redirect(url_for("home", code = 6))
        else:
            values = []
            for key in request.form:
                values.append(request.form.getlist(key)[0])
            editCategory(values[0], user["token"], values[1], values[2])
            return redirect(url_for("home", code = 5))
    else:
        return redirect(url_for("home"))


@app.route("/editcategory/<eid>")
def editCategories(eid):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    if getCategory(user["token"], eid) == 0:
        return redirect(url_for("home", code = 7))
    category = getCategory(user["token"], eid)
    return render_template("editcategory.html", category = category)


@app.route("/add", methods = ["GET", "POST"])
def addexp():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    category = updateCategory(user["token"])

    values = []
    if request.method == "POST":
        for key in request.form:
            values.append(request.form.getlist(key)[0])
        add_expense(user["token"], values[0], values[1], values[2], values[3], values[4])
        return redirect(url_for("home", code = 1))
    else:
        return render_template("add.html", category = category, date = datetime.datetime.now().strftime("%Y-%m-%d"))


@app.route("/edit", methods = ["GET", "POST"])
def edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "Supprimer":
            deleteExpense(request.form.get("id"), user["token"])
            return redirect(url_for("home", code = 3))
        else:
            values = []
            for key in request.form:
                values.append(request.form.getlist(key)[0])
            editExpense(values[0], user["token"], values[1], values[2], values[3], values[4])
            return redirect(url_for("home", code = 2))
    else:
        return redirect(url_for("home"))


@app.route("/edit/<eid>")
def editExp(eid):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    category = updateCategory(user["token"])
    if getInfos(eid, user["token"]) == 0:
        return redirect(url_for("home", code = 8))
    expense = getInfos(eid, user["token"])
    return render_template("edit.html", expense = expense, category = category)


@app.route("/expenses", methods = ["GET", "POST"])
def expenses():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    liste = updateList(user["token"])
    category = updateCategory(user["token"])
    return render_template("expense.html", liste = liste, category = category)


@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    data = request.json
    value = data.get('buttonClicked', False)
    setting = data.get('buttonid', False)
    settings = db.setting.find_one({})
    if setting in settings:
        if setting == "confirmReset" and value is True:
            if db.settings.find_one({"token": user["token"], "resetAccount": True}):
                resetAccount(user["token"])
        else:
            database.settings.update_one({"token": user["token"]}, {"$set": {setting: value}})
    return jsonify({"message": "Settings updated successfully"})


@app.route("/graphs/<category>", methods=["POST", "GET"])
def graphs(category):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    if category == "all":
        date, amount = updateCourbe(user["token"])
        res = db.settings.find_one({"token": user["token"]})
        if "color" in res:
            color = f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 0.7)"
            bcolor = f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 1)"
        else:
            color = "blue"
            bcolor = "blue"
        name = str(category)
    else:
        date, amount = updateCourbe(user["token"], category)
        color, bcolor = getCategory(user["token"], None, category)
        name = str(category)

    return render_template('graph.html', date = date, amounts = amount, name = name, color = color, bcolor = bcolor, categories = updateCategory(user["token"]))


# @app.route("/graph", methods=["POST", "GET"])
# def graph():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#
#     user = database.user.find_one({"id": session["user_id"]})
#     if not user:
#         return redirect(url_for('login'))
#
#     if request.method == "POST":
#         data = request.json
#         category2 = data.get('entry', 'all')
#         return redirect(url_for('graphs', category=category2))
#     else:
#         return redirect(url_for('graphs', category = "all"))


@app.route("/import", methods=["POST", "GET"])
def importData():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    if request.method == "POST":

        i = 0
        while True:
            if f'amount-{i}' not in request.form:
                break

            amount = request.form.get(f'amount-{i}')
            date = request.form.get(f'date-{i}')
            comment = request.form.get(f'comment-{i}')
            category = request.form.get(f'category-{i}')
            virement = request.form.get(f'virement-{i}')

            insert_expense(user["token"], float(amount), date.split("-")[2], date.split("-")[1], date.split("-")[0], category, comment, virement)

            i += 1

    return redirect(url_for('home', code = 1))


@app.route('/delete', methods=['POST'])
def delete():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    selected_expenses = request.json.get('selectedExpenses', [])
    for index in selected_expenses:
        res = db.expenses.find_one({"token": user["token"], "id": int(index)})
        if res:
            deleteExpense(int(index), user["token"])
        else:
            return redirect(url_for('home', code = 8))
        pass
    return jsonify(success=True)


@app.route("/exportData", methods = ["POST", "GET"])
def exportData():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    data = []
    expenses = db.expenses.find({"token": user['token']})
    for i in expenses:
        i["date"] = f"{'' if i['day'] > 9 else '0'}{i['day']}/{'' if i['month'] > 9 else '0'}{i['month']}/{i['year']}"
        keys = ['_id', 'id', 'token', 'sharecode', 'day', 'month', 'year']
        for key in keys:
            del i[key]
        data.append(i)

    settings_data = []
    settings = db.settings.find({"token": user['token']})
    for i in settings:
        del i["_id"]
        del i["token"]
        settings_data.append(i)

    category_data = []
    category = db.category.find({"token": user['token']})
    for i in category:
        del i["_id"]
        del i["id"]
        del i["token"]
        category_data.append(i)

    tempFile = BytesIO()
    with pd.ExcelWriter(tempFile) as writer:
        df_expenses = pd.DataFrame(data)
        df_expenses.to_excel(writer, sheet_name='Expenses', index=False)

        df_settings = pd.DataFrame(settings_data)
        df_settings.to_excel(writer, sheet_name='Settings', index=False)

        df_category = pd.DataFrame(category_data)
        df_category.to_excel(writer, sheet_name='Category', index=False)

    tempFile.seek(0)
    return send_file(tempFile, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", download_name='Expense-Tracker Datas.xlsx')
    # return redirect(url_for('settings'))

@app.route("/user-settings", methods=["POST", "GET"])
def userSettings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    if request.method == "POST":
        password = request.form['password']
        email = request.form['email']
        if hash_string(password) == user["password"]:
            settings = db.user.find_one({})
            for key in request.form:
                if key in settings:
                    if key == "password":
                        continue
                    if key == "email":
                        req = db.user.find_one({"email": email})
                        if req is None:
                            db.user.update_one({"token": user["token"]}, {"$set": {key: request.form.getlist(key)[0]}})
                        if req and req["token"] == user["token"]:
                            db.user.update_one({"token": user["token"]}, {"$set": {key: request.form.getlist(key)[0]}})
                        else:
                            redirect(url_for('home', code = 13))
                    if key == "username":
                        req = db.user.find_one({"username": request.form['username']})
                        if req is None:
                            db.user.update_one({"token": user["token"]}, {"$set": {key: request.form.getlist(key)[0]}})
                        if req and req["token"] == user["token"]:
                            db.user.update_one({"token": user["token"]}, {"$set": {key: request.form.getlist(key)[0]}})
                        else:
                            redirect(url_for('home', code = 13))
                else:
                    return redirect('home', code = 15)
            return redirect(url_for('settings'))
        return redirect(url_for('home', code = 9))
    return redirect(url_for('settings'))



@app.route("/settings", methods=["POST", "GET"])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    settings = db.setting.find()
    stg = {}
    for setting in settings:
        for key in setting:
            if key == "_id":
                continue
            stg[key] = setting[key]
    datas = db.settings.find_one({"token": user["token"]})

    newslist = []

    news = db.news.find()
    for i in news:
        newslist.append(i)

    if request.method == "POST":
        for key in request.form:
            if key == "import" and request.form.getlist("import") != ['']:
                filetype = request.form.getlist(key)[0].split(".")[1]
                authorizedFileType = ["csv", "xls", "xlsx"]
                if filetype in authorizedFileType:
                    df = pd.read_excel(request.form.getlist(key)[0], sheet_name="Category")
                    data = []
                    for i in range(len(df)):
                        row = df.iloc[i]
                        data.append(row.to_dict())
                    for category in data:
                        i = database.category.find_one({}, sort = [("id", -1)])
                        db.category.insert_one({"id": i["id"] + 1, "token": user['token'], **category})

                    df = pd.read_excel(request.form.getlist(key)[0], sheet_name="Settings")
                    data = []
                    for i in range(len(df)):
                        row = df.iloc[i]
                        data.append(row.to_dict())

                    stgs = db.setting.find_one({})
                    for settings in data:
                        for setting in settings:
                            if setting in stgs:
                                db.settings.update_one({"token": user['token']}, {"$set": {setting: settings[setting]}})

                    df = pd.read_excel(request.form.getlist(key)[0], sheet_name="Expenses")
                    data = []
                    for i in range(len(df)):
                        row = df.iloc[i]
                        data.append(row.to_dict())

                    for i in data:
                        i["date"] = datetime.datetime.strptime(i["date"], '%d/%m/%Y').strftime('%Y-%m-%d')

                    data = list(enumerate(data))
                    return render_template('import.html', data = data, categories = updateCategory(user["token"]))
                else:
                    return redirect(url_for('home', code = 14))
            if key == "budget":
                db.user.update_one({"token": user["token"]}, {"$set": {key: float(request.form.getlist(key)[0])}})
            if key == "currency":
                db.settings.update_one({"token": user["token"]}, {"$set": {"currency": request.form.getlist(key)[0]}})
            if key == "color":
                db.settings.update_one({"token": user["token"]}, {"$set": {"color": request.form.getlist(key)[0]}})
        return redirect(url_for('settings'))
    else:
        return render_template("settings.html", user = user, settings = stg, data = datas, news = newslist, currencies = getCurrencies())


@app.route("/forgotten", methods=['GET', 'POST'])
def forgotten():
    return redirect(url_for('login'))
#     if request.method == "POST":
#        email = request.form["email"]
#        uemail = db.user.find_one({"email": email})
#        if uemail is None:
#            return redirect(url_for('login', code = 13))
#        else:
#            n = db.forgotten.find_one({"email": email})
#            if n is None or datetime.datetime.now().timestamp() > n["expiration"]:
#             code = generateToken(7, random.randint(10, 15))
#             db.forgotten.insert_one({"email": email, "code": code, "expiration": datetime.datetime.now().timestamp() + 300})
#        return redirect(url_for('fcode', email = email))
#     else:
#         return render_template("forgotten.html")


# @app.route("/forgotten/code", methods=['GET', 'POST'])
# def fcode():
#     email = request.args.get('email', default = None, type = str)
#     if request.method == "POST":
#         code = request.form["code"]
#        t = db.forgotten.find_one({"email": email, "code": code})
#         if t is None:
#             redirect(url_for('login'))
#         else:
#             return redirect(url_for())
#         return redirect(url_for('/forgotten/code'))
#     else:
#         return render_template("code.html")


@app.route('/news', methods=['GET', 'POST'])
def news():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    val = []

    if request.method == 'POST':
        for key in request.form:
            values = request.form.getlist(key)
            if key == "title":
                values[0] = values[0].replace(" ", "-")
            val.append(values[0])
        db.news.insert_one({"title": val[0], "content": val[1], "creationDate": datetime.datetime.now().timestamp()})
        return redirect(url_for('home'))
    else:
        return render_template('news.html')


@app.route("/sharecode")
def sharecode():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = database.user.find_one({"id": session["user_id"]})
    if not user:
        return redirect(url_for('login'))

    # liste = updateList(user["token"])
    # for expense in liste:
        # if expense['sharecode'] == sharecode:
            # print(expense['date'])
    # add_expense(user["token"], expense['amount'], expense['date'], expense['comment'], expense['category'], expense['virement'])
    # return redirect(url_for("home", code = 1))

    return redirect(url_for("home"))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()
