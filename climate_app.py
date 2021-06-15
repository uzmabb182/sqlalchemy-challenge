import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
import datetime as dt
from dateutil.relativedelta import relativedelta
from sqlalchemy import and_

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Welcome to the Hawaii Climate Analysis API!</h1>"
        f"<h2>Available API Endpoints:</h2><br/>"

        f"<h3>PRECIPITATIONS:</h3><br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/><br/><br/><br/>"

        f"<h3>STATIONS:</h3><br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/><br/><br/><br/>"

        f"<h3>TEMPERATURE OBSERVATIONS:</h3><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/><br/><br/><br/>"

        f"<h3>START DATE:</h3><br/>"
        f"/api/v1.0/temp/MM-DD-YYYY<br/><br/><br/><br/>"

        f"<h3>START DATE & END DATE:</h3><br/>"
        f"/api/v1.0/temp/MM-DD-YYYY/MM-DD-YYYY"
    )

##########################################################################################
@app.route("/api/v1.0/precipitation") 
# Convert the query results to a dictionary using `date` as the key and `prcp` as the value.
# Return the JSON representation of your dictionary.
def precipitation():
    # Connect to database
    session = Session(engine)

    # Find the most recent date in the data set.
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    # Converting str type date into datetime
    recent_date = dt.datetime.strptime(recent_date, '%Y-%m-%d')
    # 12 month relativedelta
    twelve_mon_rel = relativedelta(months=12)
    # Query for the previous date--12 months from '2017-08-23'` using the datetime library
    query_date = recent_date - twelve_mon_rel
    # Using this date, find the average precipitation per day

    # for the preceding 12 months of data sorted by ascending date. 
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(and_(Measurement.date >= query_date,\
                Measurement.date <= recent_date)).\
                group_by(func.strftime("%d", Measurement.date)).\
                order_by(Measurement.date).all() 

    # Converting the query results into dictionary
    prcp_dict = {}
    for row in results:
        prcp_dict[row[0]] = row[1]
       
         

    # Disconnect from database
    session.close()
    return jsonify(prcp_dict)

##########################################################################################
@app.route("/api/v1.0/stations")
# Return a JSON list of stations from the dataset.
def stations():
    # Connect to database
    session = Session(engine)

    # list of stations from the dataset.

    stations_list = session.query(Measurement.station).\
                        group_by(Measurement.station).\
                        order_by(Measurement.station).all()

    stations_list = list(np.ravel(stations_list))

    # Disconnect from database
    session.close()
    return jsonify(stations_list)


##########################################################################################
@app.route("/api/v1.0/tobs")
# Return a JSON list of temperature observations (TOBS) for the previous year.
def tobs():
    # Connect to database
    session = Session(engine)

    # Find the most recent date in the data set.
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    # Converting str type date into datetime
    recent_date = dt.datetime.strptime(recent_date, '%Y-%m-%d')
    # 12 month relativedelta
    twelve_mon_rel = relativedelta(months=12)
    # Query for the previous date--12 months from '2017-08-23'` using the datetime library
    query_date = recent_date - twelve_mon_rel

    # List the most active stations and the counts in descending order.

    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
                        group_by(Measurement.station).\
                        order_by(func.count(Measurement.station).desc()).all()
    # Retrieving the first row of of most active stations
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
                        group_by(Measurement.station).\
                        order_by(func.count(Measurement.station).desc()).first()
     # Convert list of tuples into normal list and retrieving 'station name'
    greatest_num_obs = list(np.ravel(active_stations))
    station_name = greatest_num_obs[0]                      
    # Query the dates and temperature observations of the most 
    # active station for for the most recent 12 months of data.
    results = session.query(Measurement.date, Measurement.tobs).\
            filter(and_(Measurement.date >= query_date,\
                    Measurement.date <= recent_date,\
                    Measurement.station == station_name)).all()               
    
    # Converting into dictionary
    tobs_dict = {}
    for row in results:
        tobs_dict[row[0]] = row[1]
   

    # Disconnect from database
    session.close()
    return jsonify(tobs_dict)

##########################################################################################
@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
# Return a JSON list of the minimum temperature, the average temperature, 
# and the max temperature for a given start or start-end range.
def start_and_end(start='', end=''):
    if start == '':
        return 'Please provide a date in the format of YYYY-MM-DD'

    if (start != '') & (end == ''):

        # Connect to database
        session = Session(engine)
        # Create a query that returns the minimum temperature, the average temperature,
        # and the max temperature for a given start.
        # put the columns what you want to see in the output in 'sel' list 


        #sel = [Measurement.date,
        sel = [func.min(Measurement.tobs), 
            func.avg(Measurement.tobs),  
            func.max(Measurement.tobs)]           
        # Now query from sel data columns '
        # .all() takes the result and puts into a list of tuples
        start_date_aggregates = session.query(*sel).filter(Measurement.date == (start)).all() 
        # Convert list of tuples into normal list and retrieving 'station name'        
        start_temps_filtered_by_date = list(np.ravel(start_date_aggregates))   

        # Disconnect from database
        session.close()
        return jsonify(start_temps_filtered_by_date)

    if (start != '') & (end != ''):
        # Create a query that returns the minimum temperature, the average temperature,
        # and the max temperature for a given start-end range.
        # put the columns what you want to see in the output in 'sel' list 

        # Connect to database
        session = Session(engine)

        sel = [func.min(Measurement.tobs), 
            func.avg(Measurement.tobs),  
            func.max(Measurement.tobs)]
                

        # Now query from sel data columns '
        # .all() takes the result and puts into a list of tuples

        range_aggregates = session.query(*sel).\
            filter(and_(Measurement.date >= start), (Measurement.date <= end)).all() 

        # Convert list of tuples into normal list and retrieving 'station name'        
        start_end_temps_filtered_by_date = list(np.ravel(range_aggregates))   

        # Disconnect from database
        session.close()
        return jsonify(start_end_temps_filtered_by_date)

##########################################################################################

if __name__ == '__main__':
    app.run(debug=True)