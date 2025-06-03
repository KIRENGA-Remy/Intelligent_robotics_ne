from flask import Flask, render_template, jsonify, request
from database import ParkingDatabase
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)  

app = Flask(__name__)
db = ParkingDatabase()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/vehicles')
def get_vehicles():
    try:
        vehicles = db.get_all_vehicles()
        return jsonify({'success': True, 'vehicles': vehicles})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/unauthorized_exits')
def get_unauthorized_exits():
    try:
        exits = db.get_unauthorized_exits()
        return jsonify({'success': True, 'exits': exits})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/statistics')
def get_statistics():
    try:
        stats = {
            'total_vehicles': db.get_total_vehicles(),
            'current_vehicles': db.get_current_vehicles(),
            'total_revenue': db.get_total_revenue(),
            'unauthorized_exits': db.get_unauthorized_exits_count()
        }
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 