from flask import jsonify
from flask_restful import reqparse, abort, Resource

from data.audiofiles import Audiofile
from data import db_session

parser = reqparse.RequestParser()
parser.add_argument('path_to_file', required=True)
parser.add_argument('title', required=True)
parser.add_argument('author', required=True)
parser.add_argument('posted', required=True, type=int)
parser.add_argument('date_time', required=True)


def abort_if_audiofile_not_found(file_id):
    with db_session.create_session() as db_sess:
        file = db_sess.query(Audiofile).get(file_id)
        if not file:
            abort(404, message=f"File {file_id} not found")


class AudiofileListResource(Resource):
    def get(self):
        with db_session.create_session() as db_sess:
            files = db_sess.query(Audiofile).all()
            return jsonify({'files': [file.to_dict(
                only=('path_to_file', 'title', "author", "posted", "date_time")) for file in files]})

    def post(self):
        args = parser.parse_args()
        with db_session.create_session() as db_sess:
            file = Audiofile(
                path_to_file=args['path_to_file'],
                title=args['title'],
                author=args['author'],
                posted=args['posted'],
                date_time=args['date_time']
            )
            db_sess.add(file)
            db_sess.commit()
            return jsonify({'id': file.id})


class AudiofileResource(Resource):
    def get(self, file_id):
        abort_if_audiofile_not_found(file_id)
        with db_session.create_session() as db_sess:
            file = db_sess.get(Audiofile, file_id)
            return jsonify({'file': file.to_dict(
                only=('path_to_file', 'title', "author", "posted", "date_time"))})

    def put(self, file_id):
        abort_if_audiofile_not_found(file_id)
        args = parser.parse_args()
        with db_session.create_session() as db_sess:
            file = db_sess.get(Audiofile, file_id)
            file.path_to_file = args.get('path_to_file', file.path_to_file)
            file.title = args.get('title', file.title)
            file.author = args.get('author', file.author)
            file.posted = args.get('posted', file.posted)
            file.date_time = args.get('date_time', file.date_time)
            db_sess.commit()
            return jsonify({'id': file.id})
