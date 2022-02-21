# 3) do it for multiple cars
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import mysql.connector
import pandas as pd
import yaml
from flask import request, render_template

app = Flask(__name__)

# Initialize the database
db = yaml.safe_load(open("db.yaml"))
app.config["MYSQL_HOST"] = db["mysql_host"]
app.config["MYSQL_USER"] = db["mysql_user"]
app.config["MYSQL_PASSWORD"] = db["mysql_password"]
app.config["MYSQL_DB"] = db["mysql_db"]

mysql = MySQL(app)

# TODO: NEEDS TO ASSURE THAT ALL THE VALUES IN THE FORM ARE
# FILLED CORRECTLY, OTHERWISE IT MIGHT CRASH.
@app.route("/", methods=["GET", "POST"])
def home():
    # create a cursor to execute queries.
    if request.method == "POST":
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Users (Age, Gender, Location, own_license, Main_reason, \
        How_often, Important_categories, Important_emissions, Most_important)  \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                request.form["Age"],
                request.form["Gender"],
                request.form["Location"],
                request.form.get("own_license"),
                "-".join(request.form.getlist("main_reason")),
                request.form.get("How_often"),
                "-".join(request.form.getlist("important_categ")),
                request.form.get("rate"),
                "-".join(request.form.getlist("most_important")),
            ),
        )
        mysql.connection.commit()
        cur.close()
        print("A user has been added to the database succesfully.")
        return redirect(url_for("car_review"))
    else:
        return render_template("index.html")


@app.route("/car_review", methods=["GET", "POST"])
def car_review():
    # sample 1 random car.
    cur = mysql.connection.cursor()
    cur.execute("SHOW COLUMNS FROM cars.cars_new;")
    result = cur.fetchall()
    column_names = [i[0] for i in result]
    resultValue = cur.execute(
        "SELECT * FROM cars.cars_new \
        ORDER BY RAND() \
    LIMIT 1"
    )
    cars = cur.fetchall()
    my_car = pd.DataFrame(cars, columns=column_names)
    # take the path to the image and the car id so as to save it for the review.
    path_image = my_car["path_image"].values[0]
    car_id = my_car["ID"].values[0]
    # What to do when the user press submit.
    # We first, get the user id, then we save the car id and the review rate of the car.
    if request.method == "POST":
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM cars.Users;")
        result = cur.fetchall()
        user_id = result[0][0]
        print("User id:" + str(user_id))
        rate_of_car = request.form.get("rate")
        print("Rate of car:", rate_of_car)
        # create a cursor to execute queries.
        cur.execute(
            "INSERT INTO cars.Reviews (Review_Number, user_id, car_id) VALUES (%s, %s, %s)",
            (rate_of_car, user_id, car_id),
        )
        print("The sql query was executed successfully in Reviews table.")
        # count how many times the user rated a car.
        mysql.connection.commit()
        cur.close()
        # redirect to final page.
        return redirect(url_for("final_page"))
    else:
        # sample n=5 columns from the car dataframe and append maker Model.
        rand_col = (
            my_car.loc[
                :,
                ~my_car.columns.isin(
                    ["ID", "path_image", "Maker_model", "Make", "Model"]
                ),
            ]
            .sample(n=7, axis="columns")
            .columns
        )
        # convert it to a list so we can append Maker_model.
        rand_col = list(rand_col)
        rand_col.append("Maker_model")
        # return the template and the car so we can see it.
        if resultValue > 0:
            return render_template(
                "Car_review.html",
                cars=[
                    my_car[rand_col]
                    .set_index("Maker_model")
                    .to_html(classes="table table-striped")
                ],
                titles=column_names,
                img_data=path_image,
                car_name=my_car["Maker_model"].values[0],
            )


@app.route("/final_page")
def final_page():
    return "Thanks for submitting the review!"


if __name__ == "__main__":
    app.run(debug=True)
