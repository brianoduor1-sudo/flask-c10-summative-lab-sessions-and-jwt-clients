from flask import Flask, request, session
from flask_restful import Api, Resource
from flask_migrate import Migrate
from config import Config
from models import db, bcrypt, User, Note
from schemas import user_schema, note_schema, notes_schema

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# Helper function to get currently authenticated user from session
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


# --- AUTHENTICATION ROUTES ---

class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'error': 'Username and password are required.'}, 400

        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists.'}, 422

        user = User(username=username)
        user.password_hash = password

        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        return user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user_schema.dump(user), 200

        return {'error': 'Invalid username or password.'}, 401


class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id', None)
            return {}, 204
        return {'error': 'Unauthorized'}, 401


class CheckSession(Resource):
    def get(self):
        user = get_current_user()
        if user:
            return user_schema.dump(user), 200
        return {'error': 'Unauthorized'}, 401


# --- USER-OWNED RESOURCE ROUTES (NOTES) ---

class NoteListResource(Resource):
    def get(self):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        # Query parameter pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        pagination = Note.query.filter_by(user_id=user.id).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'items': notes_schema.dump(pagination.items)
        }, 200

    def post(self):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json() or {}
        title = data.get('title')
        content = data.get('content')
        category = data.get('category', 'General')

        if not title or not content:
            return {'error': 'Title and content are required.'}, 400

        note = Note(
            title=title,
            content=content,
            category=category,
            user_id=user.id
        )

        db.session.add(note)
        db.session.commit()

        return note_schema.dump(note), 201


class NoteDetailResource(Resource):
    def patch(self, id):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        # Strict ownership check
        note = Note.query.filter_by(id=id, user_id=user.id).first()
        if not note:
            return {'error': 'Note not found or access denied.'}, 404

        data = request.get_json() or {}
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = data['content']
        if 'category' in data:
            note.category = data['category']

        db.session.commit()
        return note_schema.dump(note), 200

    def delete(self, id):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        # Strict ownership check
        note = Note.query.filter_by(id=id, user_id=user.id).first()
        if not note:
            return {'error': 'Note not found or access denied.'}, 404

        db.session.delete(note)
        db.session.commit()

        return {}, 204


# Endpoint mappings
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

api.add_resource(NoteListResource, '/notes')
api.add_resource(NoteDetailResource, '/notes/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)