#/usr/bin/env python

"""A simple Kanban board application using Flask and SQLLite"""

from threading import Thread
import os
import uuid
from flask import Flask, send_from_directory, request, abort, make_response
from flask.json import jsonify
from PIL import Image
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename
from io import BytesIO


import cards


class NetworkAPI(Thread):

    def __init__(self, kanban_db):
        """Create a new instance of the flask app"""
        super(NetworkAPI, self).__init__()

        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.app.config['kanban.columns'] = ['To Do', 'Doing', 'Done']
        self.app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])
        self.app.config['port'] = 5001
        self.app.config['app_name'] = "Kanban Board"
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16mb is enough
        self.kanban_db = kanban_db
        self.kanban_db.init_app(self.app)
        self.app.app_context().push()
        self.kanban_db.create_all()

        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        print("Starting %s on port %d" % (self.app.config['app_name'], self.app.config['port']))

        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/static/<path:path>", view_func=self.static_file, methods=['GET'])
        self.app.add_url_rule(rule="/images/<path:path>", view_func=self.image_file, methods=['GET'])
        self.app.add_url_rule(rule="/cards", view_func=self.get_cards, methods=['GET'])
        self.app.add_url_rule(rule="/columns", view_func=self.get_columns, methods=['GET'])
        self.app.add_url_rule(rule="/card", view_func=self.create_card, methods=['POST'])
        self.app.add_url_rule(rule="/card/reorder", view_func=self.order_cards, methods=['POST'])
        self.app.add_url_rule(rule="/card/<int:card_id>", view_func=self.update_card, methods=['PUT'])
        self.app.add_url_rule(rule="/card/<int:card_id>", view_func=self.delete_card, methods=['DELETE'])
        self.app.add_url_rule(rule="/upload-file/<int:card_id>", view_func=self.upload_file, methods=['POST'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def run(self):
        self._server.serve_forever()

    def not_found(self, error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    def index(self):
        """Serve the main index page"""
        return send_from_directory('static', 'index.html')
    
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.app.config['ALLOWED_EXTENSIONS']

    # http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
    def upload_file(self, card_id):
    
        file_data = request.form.get('file_data')
        new_file_name = request.form.get('new_file_name')
        file_name = request.form.get('file_name')
        if (file_data is None or new_file_name is None or file_name is None):
            abort(400)
        
        encoded_file_data = file_data.split(',')[1] #cut "data:image/jpeg;base64,"
        im = Image.open(BytesIO(encoded_file_data.decode('base64')))
        
        final_path = os.path.normpath(os.path.join(self.app.config['UPLOAD_FOLDER'], new_file_name))
        im.save(final_path, "JPEG")
        self.delete_card_image(card_id)
        cards.update_card_image(card_id, file_name, new_file_name)
        return 'Success'  
        
    def static_file(self, path):
        """Serve files from the static directory"""
        return send_from_directory('static', path)

    def image_file(self, path):
        """Serve files from the images directory"""
        return send_from_directory('images', path)

    def get_cards(self):
        """Get an order list of cards"""
        return jsonify(cards.all_cards())

    def get_columns(self):
        """Get all valid columns"""
        return jsonify(self.app.config.get('kanban.columns'))

    def create_card(self):
        """Create a new card"""

        # TODO: validation
        cards.create_card(
                text=request.form.get('text'),
                column=request.form.get('column', self.app.config.get('kanban.columns')[0]),
        )

        # TODO: handle errors
        return 'Success'

    def order_cards(self):
        """Reorder cards by moving a single card

        The JSON payload should have a 'card' and 'before' attributes where card is
        the card ID to move and before is the card id it should be moved in front
        of. For example:

        {
                "card": 3,
                "before": 5,
        }

        "before" may also be "all" or null to move the card to the beginning or end
        of the list.
        """

        if not request.is_json:
            abort(400)
        cards.order_cards(request.get_json())
        return 'Success'

    def update_card(self, card_id):
        """Update an existing card, the JSON payload may be partial"""
        if not request.is_json:
            abort(400)

        # TODO: handle errors
        cards.update_card(card_id, request.get_json(), self.app.config.get('kanban.columns'))

        return 'Success'

    def delete_card(self, card_id):
        """Delete a card by ID"""

        # delete filename
        self.delete_card_image(card_id)
        
        # TODO: handle errors
        cards.delete_card(card_id)
        return 'Success'
        
    def delete_card_image(self, card_id):
        card_image_name = cards.get_card_file(card_id)
        if card_image_name is not None:
            final_name = os.path.join(self.app.config['UPLOAD_FOLDER'], card_image_name)
            os.remove(final_name)
