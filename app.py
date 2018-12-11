#/usr/bin/env python

"""A simple Kanban board application using Flask and SQLLite"""

from threading import Thread
from flask import Flask, send_from_directory, request, abort, make_response
from flask.json import jsonify
from werkzeug.serving import make_server

import cards

class NetworkAPI(Thread):

	def __init__(self, kanban_db):
		"""Create a new instance of the flask app"""
		super(NetworkAPI, self).__init__()
		
		self.app = Flask(__name__)
		self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
		self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
		self.app.config['kanban.columns'] = ['To Do', 'Doing', 'Done']
		self.kanban_db = kanban_db
		self.kanban_db.init_app(self.app)
		self.app.app_context().push()
		self.kanban_db.create_all()
		
		self._server = make_server(host='0.0.0.0', port=5001, app=self.app, threaded=True)

		# register some endpoints
		self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
		self.app.add_url_rule(rule="/static/<path:path>", view_func=self.static_file, methods=['GET'])
		self.app.add_url_rule(rule="/cards", view_func=self.get_cards, methods=['GET'])
		self.app.add_url_rule(rule="/columns", view_func=self.get_columns, methods=['GET'])
		self.app.add_url_rule(rule="/card", view_func=self.create_card, methods=['POST'])
		self.app.add_url_rule(rule="/card/reorder", view_func=self.order_cards, methods=['POST'])
		self.app.add_url_rule(rule="/card/<int:card_id>", view_func=self.update_card, methods=['PUT'])
		self.app.add_url_rule(rule="/card/<int:card_id>", view_func=self.delete_card, methods=['DELETE'])
		
		# register default error handler
		self.app.register_error_handler(code_or_exception=404, f=self.not_found)
    
	def run(self):
		self._server.serve_forever()

	def not_found(self, error):
		return make_response(jsonify({'error': 'Not found'}), 404)

	def index(self):
		"""Serve the main index page"""
		return send_from_directory('static', 'index.html')

	def static_file(self, path):
		"""Serve files from the static directory"""
		return send_from_directory('static', path)

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
			color=request.form.get('color', None),
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

	def delete_card(card_id):
		"""Delete a card by ID"""

		# TODO: handle errors
		cards.delete_card(card_id)
		return 'Success'
