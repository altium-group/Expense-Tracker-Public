import datetime, string, random, requests
from pymongo.mongo_client import MongoClient

uri = "mongodb+srv://noanh07:5Pn3wmjC3IIcME7y@expense-tracker.0wqemg6.mongodb.net/?retryWrites=true&w=majority&appName=Expense-Tracker"
client = MongoClient(uri)
db = client["Expense-Tracker"]


def summary(token):
    totals = ""
    expenses = db["expenses"]
    result = expenses.aggregate([{"$match": {"virement": False, "token": token}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}])
    totalLabel = 0
    for i in result:
        totalLabel = i.get("total", 0)
    result = expenses.aggregate([{"$match": {"virement": False, "token": token}}, {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}, {"$sort": {"total": 1}}])

    catt = {doc["_id"]: doc["total"] for doc in result}
    for index, row in enumerate(catt):
        totals += f"{row} : {isCurrencyBefore(catt[row], token)}"
        if index < len(catt) - 1:
            totals += ", "
        if (index + 1) % 5 == 0:
            totals += "<br>"
    return totalLabel, totals


def updateList(token):
    liste = []
    expenses = db["expenses"]
    result = expenses.find({"token": token})
    for res in result:
        app = {"date": f"{'' if res['day'] > 9 else '0'}{res['day']}/{'' if res['month'] > 9 else '0'}{res['month']}/{res['year']}", "day": res['day'], "month": res['month'], "year": res['year'], "virement": res["virement"], "amount": f"{'+' if res['virement'] == True else '-'} {isCurrencyBefore(res['amount'], token)}", "comment": res["comment"], "category": res["category"], "time": datetime.datetime.fromtimestamp(res["time"]).strftime('%d/%m/%Y'), "iso": datetime.datetime.fromtimestamp(res["time"]).strftime('%Y-%m-%d'), "sharecode": res["sharecode"], "id": res["id"]}
        liste.append(app)

    sort = sorted(liste, reverse = True, key = lambda x: datetime.datetime(x["year"], x["month"], x["day"]))
    return sort


def updateCourbe(token, category = None):
    expenses = db["expenses"]
    date = []
    amounts = []
    if category is None or category == "all":
        result = expenses.aggregate([{"$match": {"virement": False, "token": token}}, {"$group": {"_id": {"month": "$month", "year": "$year"}, "total_amount": {"$sum": "$amount"}}}, {"$sort": {"_id.year": 1, "_id.month": 1}}])

        for row in result:
            date.append(f"{'' if row['_id']['month'] > 9 else '0'}{row['_id']['month']}/{row['_id']['year']}")
            amounts.append(row["total_amount"])
        return date, amounts
    if category is not None:
        result = expenses.aggregate([{"$match": {"virement": False, "token": token, "category": category}}, {"$group": {"_id": {"month": "$month", "year": "$year"}, "total_amount": {"$sum": "$amount"}}}, {"$sort": {"_id.year": 1, "_id.month": 1}}])

        for row in result:
            date.append(f"{'' if row['_id']['month'] > 9 else '0'}{row['_id']['month']}/{row['_id']['year']}")
            amounts.append(row["total_amount"])
        return date, amounts


def updateCategoryCourbe(token):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("SELECT month, year, SUM(amount), category AS total_amount FROM expenses WHERE virement = 'False' AND token = ? GROUP BY category, month, year ORDER BY year, month", (token,))
    data = c.fetchall()
    category = {}

    for row in data:
        category_name = row[3]
        if category_name not in category:
            category[category_name] = {'date': [], 'amount': [], 'color': ''}

        date = f"{'' if row[0] > 9 else '0'}{row[0]}/{row[1]}"
        amounts = row[2]

        c.execute("SELECT color FROM category WHERE name = ?", (category_name,))
        result = c.fetchone()
        color = f"rgba({hex_to_rgb(result[0])[0]}, {hex_to_rgb(result[0])[1]}, {hex_to_rgb(result[0])[2]})"

        category[category_name]['date'].append(date)
        category[category_name]['amount'].append(amounts)
        category[category_name]['color'] = color

    conn.close()
    return category


def updateChart(token):
    expenses = db["expenses"]
    result = expenses.aggregate([{"$match": {"virement": False, "token": token}}, {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}, {"$sort": {"total": 1}}])

    data = {doc["_id"]: doc["total"] for doc in result}
    labels = []
    datas = []
    color = []
    bcolor = []
    for item in data:
        labels.append(item)
        datas.append(data[item])
    for label in labels:
        category = db["category"]
        res = category.find_one({"name": label, "token": token})
        color.append(f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 0.7)")
        bcolor.append(f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 1)")
    return labels, datas, color, bcolor


def insert_sql_expense(token, amount, day, month, year, category, comment, virement):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (token, amount, day, month, year, category, commentaire, virement, time, sharecode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (token, amount, day, month, year, category, comment, virement, datetime.datetime.now().timestamp(), generateToken(5, 10)), )
    conn.commit()
    conn.close()


def insert_expense(token, amount, day, month, year, category, comment, virement):
    collection = db["expenses"]
    vrm = True if virement == "True" else False
    res = collection.find_one({}, sort = [("id", -1)])
    if res is not None:
        app = {"id": res["id"] + 1, "token": token, "amount": float(amount), "day": int(day), "month": int(month), "year": int(year), "category": category, "comment": comment, "virement": vrm, "time": datetime.datetime.now().timestamp(), "sharecode": generateToken(5, 10)}
    else:
        app = {"id": 0, "token": token, "amount": float(amount), "day": int(day), "month": int(month), "year": int(year), "category": category, "comment": comment, "virement": vrm, "time": datetime.datetime.now().timestamp(), "sharecode": generateToken(5, 10)}
    collection.insert_one(app)


def updateBudget(token):
    user = db["user"]
    result = user.find_one({"token": token})
    return result["budget"]


def add_sql_expense(token, amount, date, comment, category, virement):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    year, month, day = date.split("-")
    insert_expense(token, amount, day, month, year, category, comment, virement)
    c.execute("SELECT budget FROM user WHERE token = ?", (token,))
    result = c.fetchone()
    if virement == "True":
        c.execute("UPDATE user SET budget = ? WHERE token = ?", (result[0] + float(amount), token))
    else:
        c.execute("UPDATE user SET budget = ? WHERE token = ?", (result[0] - float(amount), token))
    conn.commit()
    conn.close()


def add_expense(token, amount, date, comment, category, virement):
    user = db["user"]
    year, month, day = date.split("-")
    insert_expense(token, amount, day, month, year, category, comment, virement)
    result = user.find_one({"token": token})
    if virement == "True":
        user.update_one({"token": token}, {"$set": {"budget": result["budget"] + float(amount)}})
    else:
        user.update_one({"token": token}, {"$set": {"budget": result["budget"] - float(amount)}})


def updateCategory(token):
    category = db["category"]
    options = []
    result = category.find({"token": token})
    for i in result:
        options.append(i["name"])
    return options


def getCategory(token, id = None, name = None):
    liste = []
    category = db["category"]
    if id is None and name is None:
        result = category.find({"token": token})
        res = db.expenses.aggregate([{"$match": {"virement": False, "token": token}}, {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}, {"$sort": {"total": 1}}])

        catt = {doc["_id"]: doc["total"] for doc in res}

        tots = db.expenses.aggregate([{"$match": {"virement": False, "token": token}}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}])
        totalLabel = 0
        for i in tots:
            totalLabel = i.get("total", 0)

        for i in result:
            if i["name"] in catt:
                liste.append({"name": i["name"], "color": i["color"], "id": i["id"], "total": catt[i["name"]], "percent": f"{round(int(catt[i['name']]) / int(totalLabel) * 100, 2)}%"})
            else:
                liste.append({"name": i["name"], "color": i["color"], "id": i["id"], "total": 0, "percent": "0%"})
        return liste
    if id is not None:
        result = category.find_one({"token": token, "id": int(id)})
        if result is None:
            return 0
        app = {"name": result["name"], "color": result["color"], "id": id}
        return app
    else:
        res = category.find_one({"name": name, "token": token})
        color = f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 0.7)"
        bcolor = f"rgba({hex_to_rgb(res['color'])[0]}, {hex_to_rgb(res['color'])[1]}, {hex_to_rgb(res['color'])[2]}, 1)"
        return color, bcolor


def addCategory(token, name, color):
    category = db["category"]
    result = category.find_one({"name": name[0], "token": token})
    res = category.find_one({}, sort = [("id", -1)])
    if result is None:
        category.insert_one({"id": res["id"] + 1, "token": token, "name": name[0], "color": color[0]})
    else:
        return 0


def editCategory(id, token, name, color):
    category = db["category"]
    category.update_one({"token": token, "id": int(id)}, {"$set": {"name": name, "color": color}})


def deleteCategory(id, token):
    category = db["category"]
    category.delete_one({"id": int(id), "token": token})


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    return rgb


def editExpense(id, token, amount, date, comment, category):
    expenses = db["expenses"]
    user = db["user"]
    year, month, day = date.split("-")
    result = expenses.find_one({"token": token, "id": int(id)})
    expenses.update_one({"token": token, "id": int(id)}, {"$set": {"amount": float(amount), "day": int(day), "month": int(month), "year": int(year), "comment": comment, "category": category}})
    res = user.find_one({"token": token})
    if result["virement"]:
        user.update_one({"token": token}, {"$set": {"budget": float(res["budget"]) + float(amount) - float(result["amount"])}})
    else:
        user.update_one({"token": token}, {"$set": {"budget": float(res["budget"]) + float(result["amount"]) - float(amount)}})


def getInfos(eid, token):
    expenses = db["expenses"]
    result = expenses.find_one({"token": token, "id": int(eid)})
    if result is None:
        return 0
    app = {"date": f"{result['year']}-{'' if result['month'] > 9 else '0'}{result['month']}-{'' if result['day'] > 9 else '0'}{result['day']}", "status": result['virement'], "amount": result['amount'], "comment": result['comment'], "category": result['category'], "id": result['id']}
    return app


def deleteExpense(id, token):
    user = db["user"]
    expenses = db["expenses"]
    result = expenses.find_one({"token": token, "id": int(id)})
    res = user.find_one({"token": token})
    if result['virement']:
        user.update_one({"token": token}, {"$set": {"budget": float(res['budget']) - float(result['amount'])}})
    else:
        user.update_one({"token": token}, {"$set": {"budget": float(res['budget']) + float(result['amount'])}})
    expenses.delete_one({"token": token, "id": int(id)})


def generateToken(min: int, max: int):
    all_chars = string.ascii_letters + string.digits
    password = "".join(random.choice(all_chars) for x in range(random.randint(min, max)))
    return password


def resetAccount(token):
    db.expenses.delete_many({"token": token})
    db.category.delete_many({"token": token})
    db.settings.delete_many({"token": token})
    db.user.update_one({"token": token}, {"$set": {"budget": 0, "email": None}})
    db.settings.insert_one({"token": token, "currency": "€"})
    i = db.category.find_one({}, sort = [("id", -1)])
    db.category.insert_one({"id": i["id"] + 1, "token": token, "name": "Eco", "color": "#ad3434"})


def getVersion():
    return db.infos.find_one({})


def getCurrencies():
    url = 'https://api.exchangerate-api.com/v4/latest/EUR'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        currencies = data['rates'].keys()
        return currencies
    else:
        print("Erreur lors de la récupération des devises.")
        return []


def isCurrencyBefore(value, token):
    res = db.settings.find_one({"token": token})
    if res:
        isBefore = res.get("isCurrencyBefore")
        currency = res.get("currency")
        if isBefore:
            return f"{currency}{round(value, 2):,}"
        else:
            return f"{round(value, 2):,}{currency}"

