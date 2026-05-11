from flask import jsonify
from flask_restful import reqparse, abort, Resource

from data.users import User

from data import db_session

parser = reqparse.RequestParser()
parser.add_argument('email', required=True)
parser.add_argument('nickname', required=True)
parser.add_argument('password', required=True)


def abort_if_user_not_found(user_id):
    with db_session.create_session() as db_sess:
        user = db_sess.query(User).get(user_id)
        if not user:
            abort(404, message=f"User {user_id} not found")


class UserListResource(Resource):
    def get(self):
        with db_session.create_session() as db_sess:
            users = db_sess.query(User).all()
            return jsonify({'users': [user.to_dict(
                only=('email', 'nickname')) for user in users]})

    def post(self):
        args = parser.parse_args()
        with db_session.create_session() as db_sess:
            user = User(
                email=args['email'],
                nickname=args['nickname']
            )
            user.set_password(args['password'])
            db_sess.add(user)
            db_sess.commit()
            return jsonify({'id': user.id})


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        with db_session.create_session() as db_sess:
            user = db_sess.get(User, user_id)
            return jsonify({'user': user.to_dict(
                only=('email', 'nickname'))})

    def put(self, user_id):
        abort_if_user_not_found(user_id)
        args = parser.parse_args()
        with db_session.create_session() as db_sess:
            user = db_sess.get(User, user_id)
            if user.check_password(args['password']):
                user.email = args.get('email', user.email)
                user.nickname = args.get('nickname', user.nickname)
                db_sess.commit()
                return jsonify({'id': user.id})
            abort(403, message="Passwords don't match")
            return jsonify({'status': 403})
