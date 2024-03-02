
from collections import OrderedDict

from flask import Flask, jsonify, render_template, request
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, func
from flask_bootstrap import Bootstrap5
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, URL

app = Flask(__name__)
bootstrap = Bootstrap5(app)

# Form key
app.config['SECRET_KEY'] = 'my_secret_key'

# CREATE DB
class Base(DeclarativeBase):
    pass
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'

db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    # def to_dict(self):
    #     return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def to_dict(self):
        return OrderedDict((column.name, getattr(self, column.name)) for column in self.__table__.columns)


with app.app_context():
    db.create_all()


# Add Cafe Form
class CafeForm(FlaskForm):
    name = StringField("Cafe Name", render_kw={'autofocus': True}, validators=[DataRequired(), Length(max=250)])
    map_url = StringField("Map URL", validators=[DataRequired(), URL(message="Must be a valid URL")])
    img_url = StringField("Image URL", validators=[DataRequired(), URL(message="Must be a valid URL")])
    location = StringField("Location", validators=[DataRequired(), Length(max=250)])
    seats = StringField("Number of Seats", validators=[DataRequired()])
    has_toilet = BooleanField("Has Toilet")
    has_wifi = BooleanField("Has Wi-Fi")
    has_sockets = BooleanField("Has Sockets")
    can_take_calls = BooleanField("Can Take Calls")
    coffee_price = StringField("Coffee Price", validators=[Length(max=250)])
    submit = SubmitField("Submit")


@app.route("/")
def home():
    form = CafeForm()
    return render_template("index.html", form=form)


# HTTP GET - Read Record
@app.route("/random")
def get_random_cafe():
    random_cafe = db.session.query(Cafe).order_by(func.random()).first()
    if random_cafe:
        # Access data from the random entry object
        # return jsonify(cafe={
        #     # "id": random_cafe.id,
        #     "name": random_cafe.name,
        #     "map_url": random_cafe.map_url,
        #     "img_url": random_cafe.img_url,
        #     "location": random_cafe.location,
        #
        #     "amenities": {
        #         "seats": random_cafe.seats,
        #         "has_toilet": random_cafe.has_toilet,
        #         "has_wifi": random_cafe.has_wifi,
        #         "has_sockets": random_cafe.has_sockets,
        #         "can_take_calls": random_cafe.can_take_calls,
        #         "coffee_price": random_cafe.coffee_price,
        #     }
        # })
        print(f"Retrieved random cafe: {random_cafe.name}")
        return jsonify(random_cafe.to_dict())
    else:
        print("No cafes found.")


@app.route("/all")
def get_all_cafes():
    all_cafes = db.session.query(Cafe).all()
    return jsonify([cafe.to_dict() for cafe in all_cafes])


@app.route("/search")
def search_cafe():
    cafe_location = request.args.get("loc")
    if cafe_location:
        cafes_at_loc = db.session.query(Cafe).where(Cafe.location == cafe_location).all()  # .filter OK too
        if not cafes_at_loc:
            return jsonify({"message": "No cafes found for the specified location."})
        else:
            return jsonify([cafe.to_dict() for cafe in cafes_at_loc])
    else:
        print("No location input.")


# HTTP POST - Create Record
@app.route("/add", methods=['POST'])
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        cafe_data = {field.name: field.data for field in form if field.name not in ('submit', 'csrf_token')}
        new_cafe = Cafe(**cafe_data)
        try:
            db.session.add(new_cafe)
            db.session.commit()
            print("Cafe added")
            return jsonify(response={'session': 'Cafe added successfully'})
        except IntegrityError as e:
            db.session.rollback()
            print(f"Error adding movie: {e}")
    else:
        return render_template('index.html', form=form)

# HTTP PUT/PATCH - Update Record

@app.route('/update-price/<cafe_name>', methods=['GET', 'POST'])
def update_price(cafe_name):
    cafe = db.session.query(Cafe).filter_by(name=cafe_name).first_or_404()
    # cafe = db.get_or_404(Cafe, id) # if fetching with id instead of cafe_name
    new_price = request.args.get('new_price')
    if new_price is None:
        print("Error: Missing new price parameter. Please provide 'new_price' in the query string."), 400
        return jsonify(response={'session': "Error: Missing new price parameter. Please provide 'new_price' in the query string."}), 400
    else:
        cafe.coffee_price = new_price
        db.session.commit()
    return jsonify(response={'session': 'Successfully updated the price.'})


# HTTP DELETE - Delete Record
@app.route("/delete/<cafe_name>", methods=['GET', 'POST'])
def delete_cafe(cafe_name):
    api_key = request.args.get('api_key')
    if api_key != app.config['SECRET_KEY']:
        return jsonify(response={'error': 'Invalid key'}), 401
    else:
        cafe = db.session.query(Cafe).filter_by(name=cafe_name).first_or_404()
        db.session.delete(cafe)
        db.session.commit()
        return jsonify(response={'success': 'Successuflly deleted the cafe.'})


if __name__ == '__main__':
    app.run(debug=True)


