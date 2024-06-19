from flask import Flask, render_template, request

import json

from flask_api.services.SearchService import SearchService

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('flask_api.CONFIG')
    app.secret_key = 'just-testing45'
    
    @app.route('/')
    def homepage():
        return render_template('homepage.html')
    
    @app.route('/search', methods=['GET','POST'])
    def search():
        query = request.form.get('q') or request.args.get('q')
        
        search_results = json.loads(SearchService(query=query).search())
        
        return render_template('homepage.html', search_results = search_results)
    
    
    return app