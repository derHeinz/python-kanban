"""Card model and controller"""

from datetime import datetime
from database import db


masks = [1,2,4,8,16,32,64,128,256,512]

class Tag(object):
    id= 0

    def json(self):
        return {
            'id': self.id,
        }

def calc_tags(number):
    ret = []
    for m in masks:
        val = True
        if (number & m) == 0:
            val = False
        if val:
            t = Tag()
            t.id = m
            ret.append(t)
    return ret

class Card(db.Model): # pylint: disable=too-few-public-methods
    """SQLAlchemy card class"""
    id = db.Column(db.Integer, primary_key=True) # pylint: disable=C0103
    text = db.Column(db.String(120))
    additional_text = db.Column(db.String(1000))
    column = db.Column(db.String(120), default="To Do")
    modified = db.Column(db.DateTime, default=datetime.utcnow)
    archived = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    tags = db.Column(db.Integer, default=0)
    due_date = db.Column(db.Date, default=None)
    image_name = db.Column(db.String(100))
    image_fs_name = db.Column(db.String(100))

    def __repr__(self):
        """Return a string representation of a card"""
        return '<Card (%d): %s>' % (self.id, self.text)

    def json(self):
        """Return a JSON representation of a card"""
        return {
            'id': self.id,
            'text': self.text,
            'tags': [tag.json() for tag in calc_tags(self.tags)],
            'additional_text': self.additional_text,
            'column': self.column,
            'modified': self.modified.isoformat(),
            'archived': self.archived,
            'due_date': (self.due_date.isoformat() if self.due_date is not None else None),
            'image_name': self.image_name,
            'image_fs_name': self.image_fs_name,
        }

def all_cards():
    """Return JSON for all cards, sorted by the order_by attribute"""
    return [card.json() for card in Card.query.order_by(Card.sort_order.asc()).all()]
    
def _get_card(card_id):
    return Card.query.get(card_id)
    
def get_card_file(card_id):
    card = _get_card(card_id)
    return str(card.image_fs_name)

def create_card(text, **kwargs):
    """Create a new card"""
    # TODO: handle missing values
    db.session.add(Card(text=text, **kwargs))
    db.session.commit()

def delete_card(card_id):
    """Delete a card"""
    # TODO: handle missing values
    db.session.delete(Card.query.get(card_id))
    db.session.commit()

def order_cards(data):
    """Reposition a specified card"""
    # TODO: handle missing 'card' property
    card_id = data['card']
    before_id = data.get('before', 'all')
    cards = Card.query.order_by(Card.sort_order.asc()).all()
    card = next(card for card in cards if card.id == card_id)

    if before_id is None:
        # move to end
        cards.append(cards.pop(cards.index(card)))
    elif before_id == 'all':
        # move to start
        cards.insert(0, cards.pop(cards.index(card)))
    else:
        before_card = next(card for card in cards if card.id == before_id)
        moving_card = cards.pop(cards.index(card))
        new_index = cards.index(before_card)
        cards.insert(new_index, moving_card)

    for i, card in enumerate(cards):
        card.sort_order = i #len(cards) - i

    db.session.commit()
    
def update_card_image(card_id, image_name, image_fs_name):
    card = Card.query.get(card_id)
    card.image_name = image_name
    card.image_fs_name = image_fs_name
    db.session.commit()

def update_card(card_id, json, columns):
    """Update an existing card"""
    card = Card.query.get(card_id)

    modified = False

    if 'text' in json:
        modified = True
        card.text = json['text']

    if 'column' in json:
        if json['column'] in columns:
            modified = True
            card.column = json['column']
        else:
            raise Exception("Invalid column name: %s" % json['column'])

    if 'archived' in json:
        modified = True
        card.archived = json['archived']

    if 'tags' in json:
        modified = True
        tags_int = 0
        for tag in json['tags']:
            val = tag.get('id')
            tags_int += int(val)
        card.tags = tags_int

    if 'due_date' in json:
        dd = json['due_date']
        if (dd is not None and dd != ""):
            modified = True
            card.due_date = datetime.strptime(dd, "%Y-%m-%d")
        else:
            card.due_date = None

    if modified:
        card.modified = datetime.utcnow()

    db.session.commit()
