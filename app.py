from flask import Flask, render_template, request,  redirect, url_for , make_response, flash
from flask_restful import Api, Resource , reqparse 
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import json
from datetime import datetime
import matplotlib.pyplot as plt
from model import db, User, Admin , Song , Album , Comment , Playlist
from functools import wraps


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music.sqlite3'
db.init_app(app)
api=Api(app)

app.app_context().push()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = kwargs.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implement session-based admin check here
        if 'admin_id' not in request.cookies:
            flash('Admin access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    registration_message = request.args.get('message', None)
    message = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            return redirect(f"/dashboard/{username}")
        else:
            message = {'type': 'danger', 'text': 'Invalid username or password'}

    return render_template('login.html', registration_message=registration_message, message=message)


@app.route('/admin_login', methods=['GET', 'POST'], endpoint='admin_login')
def admin_login():
    message=None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin_user = Admin.query.filter_by(username=username, password=password).first()

        if admin_user:
            return redirect(url_for('admin_dashboard'))
        else:
            message = {'type': 'danger', 'text': 'Invalid username or password'}

    return render_template('admin_login.html', message=message)
@app.route('/user_dashboard/<username>' , methods=["GET","POST"])
def user_dashboard(username):
    user = User.query.filter_by(username=username).first()
    return render_template(
            'profile_user_dashboard.html',
            user=user )

@app.route('/creator_dashboard/<username>' , methods=["GET","POST"])
def creator_dashboard(username):
    user = User.query.filter_by(username=username).first()
    if user and user.role == "creator":
        def calculate_average_rating(creator_id):
            ratings = Comment.query.filter_by(user_id=creator_id).with_entities(Comment.value).all()
            if not ratings:
                return 0
            average_rating = sum(rating[0] for rating in ratings) / len(ratings)
            return round(average_rating,2)
        total_songs = Song.query.filter_by(user_id=user.id).count()
        average_rating = calculate_average_rating(user.id) 
        total_albums = Album.query.filter_by(user_id=user.id).count()
        user_uploads = Song.query.filter_by(user_id=user.id).all()

        return render_template(
            'profile_creator_dashboard.html',
            user=user,
            total_songs=total_songs,
            average_rating=average_rating,
            total_albums=total_albums,
            user_uploads=user_uploads,
        )
    
@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    song = Song.query.filter_by(id=song_id).first()

    if song:
        if request.method == 'POST':
            updated_title = request.form.get('title')
            updated_artist = request.form.get('artist')
            updated_lyrics = request.form.get('lyrics')
            updated_release_date = request.form.get('release_date')
            song.title = updated_title
            song.artist = updated_artist
            song.lyrics = updated_lyrics
            updated_release_date = datetime.strptime(updated_release_date, '%Y-%m-%d').date()
            song.release_date  = updated_release_date
            db.session.commit()
            return redirect(url_for('creator_dashboard',username=song.user.username))
        return render_template('edit_song.html', song=song)

@app.route('/delete_song/<int:song_id>', methods=['POST'])
def delete_song(song_id):
    song = Song.query.get(song_id)
    username=song.user.username
    
    if request.method == 'POST' and song:
        db.session.delete(song)
        db.session.commit()

    return redirect(url_for('creator_dashboard', username=username))

@app.route('/admin_dashboard')
def admin_dashboard():
    def get_statistics():
        user_count = User.query.count()
        creator_count = User.query.filter_by(role='creator').count()
        song_count = Song.query.count()
        album_count = Album.query.count()
        song_artist_counts = [
            (artist, len([song.id for song in Song.query.filter_by(artist=artist).all()]))
            for artist in set(song.artist for song in Song.query.all())
        ]

        genre_count = Album.query.distinct(Album.genre).count()

        return user_count, creator_count, song_count, genre_count, album_count, song_artist_counts

    user_count, creator_count, song_count, genre_count, album_count, song_artist_counts = get_statistics()

    def generate_user_role_chart():
        labels = ['User', 'Creator', 'Admin']
        counts = [user_count, creator_count, 1]

        fig, ax = plt.subplots()
        ax.bar(labels, counts)
        ax.set_xlabel('User Role')
        ax.set_ylabel('Count')
        chart_path = 'static/user_role_chart.png'
        plt.savefig(chart_path)
        return chart_path

    def generate_song_artist_chart():
        if not song_artist_counts:
            return None

        labels, counts = zip(*song_artist_counts)

        fig, ax = plt.subplots()
        ax.bar(labels, counts)
        ax.set_xlabel('Artist')
        ax.set_ylabel('Count')
        chart_path = 'static/song_artist_chart.png'
        plt.savefig(chart_path)
        return chart_path
    user_role_chart_path = generate_user_role_chart()
    song_artist_chart_path = generate_song_artist_chart()

    return render_template(
        'admin_dashboard.html',
        user_role_chart_path=user_role_chart_path,
        song_artist_chart_path=song_artist_chart_path,
        user_count=user_count,
        creator_count=creator_count,
        song_count=song_count,
        genre_count=genre_count,
        album_count=album_count
    )
@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if request.method == 'POST':
        user_id_to_delete = request.form.get('user_id')
        if user_id_to_delete:
            user_to_delete = User.query.get(user_id_to_delete)
            if user_to_delete:
                db.session.delete(user_to_delete)
                db.session.commit()
    search_query = request.form.get('search_query', '')
    
    users = User.query

    if search_query:
        users = users.filter(User.username.ilike(f"%{search_query}%"))
        users = users.union(User.query.filter(User.role.ilike(f"%{search_query}%")))

    users = users.all()
    return render_template('user_data.html', users=users, search_query=search_query)


@app.route('/admin_creators', methods=['GET', 'POST'])
def admin_creators():
    if request.method == 'POST':
        creator_id_to_delete = request.form.get('creator_id')
        if creator_id_to_delete:
            creator_to_delete = User.query.get(creator_id_to_delete)
            if creator_to_delete:
                db.session.delete(creator_to_delete)
                db.session.commit()

    search_query = request.form.get('search_query', '')
    
    creators = User.query.filter_by(role='creator')

    if search_query:
        creators = creators.filter(User.username.ilike(f"%{search_query}%"))

    creators = creators.all()
    def get_average_rating(creator_id):
        ratings = Comment.query.filter_by(user_id=creator_id).with_entities(Comment.value).all()
        if not ratings:
            return 0
        average_rating = sum(rating[0] for rating in ratings) / len(ratings)
        return round(average_rating,2)
    
    for creator in creators:
        creator.songs = Song.query.filter_by(user_id=creator.id).all()
        creator.albums = Album.query.filter_by(user_id=creator.id).all()
        creator.average_rating = get_average_rating(creator.id)

    return render_template('admin_creators.html', creators=creators, search_query=search_query)



@app.route('/admin/songs', methods=['GET', 'POST'])
def admin_songs():
    if request.method == 'POST':
        song_id_to_delete = request.form.get('song_id')
        if song_id_to_delete:
            song_to_delete = Song.query.get(song_id_to_delete)
            if song_to_delete:
                db.session.delete(song_to_delete)
                db.session.commit()
    search_query = request.form.get('search_query', '')
    
    songs = Song.query
    if search_query:
        songs = songs.filter(Song.title.ilike(f"%{search_query}%"))
        songs = songs.union(Song.query.filter(Song.artist.ilike(f"%{search_query}%")))

    return render_template('admin_songs.html', songs=songs)

@app.route('/admin_albums', methods=['GET', 'POST'])
def admin_albums():
    if request.method == 'POST':
        album_id_to_delete = request.form.get('album_id')
        if album_id_to_delete:
            album_to_delete = Album.query.get(album_id_to_delete)
            if album_to_delete:
                db.session.delete(album_to_delete)
                db.session.commit()
    search_query = request.form.get('search_query', '')
    
    albums = Album.query

    if search_query:
        albums = albums.filter(Album.name.ilike(f"%{search_query}%"))
        albums = albums.union(Album.query.filter(Album.genre.ilike(f"%{search_query}%")))
        albums = albums.union(Album.query.filter(Album.artist.ilike(f"%{search_query}%")))

    albums = albums.all()
    
    return render_template('admin_albums.html', albums=albums, search_query=search_query)


@app.route('/register', methods=['GET', 'POST'], endpoint='register')
def register():
    message = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        mobile_number = request.form.get('mobile_number')
        address = request.form.get('address')
        is_creator = 'is_creator' in request.form

        if User.query.filter_by(username=username).first():
            message = {'type': 'danger', 'text': 'Username is already taken. Choose another one.'}
        else:
            new_user = User(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                mobile_number=mobile_number,
                address=address,
                role='creator' if is_creator else 'user'
            )

            db.session.add(new_user)
            db.session.commit()

            message = 'Registration successful! You can now log in.'
            return redirect(url_for('login', message=message))

    return render_template('register.html', message=message)

@app.route('/upload_song/<string:username>', methods=['GET', 'POST'])
def upload_song(username):
    user = User.query.filter_by(username=username).first()
    albums = Album.query.filter_by(user_id=user.id).all() if user else []

    if request.method == 'POST':
        title = request.form.get('title')
        artist = request.form.get('singer')
        release_date_str = request.form.get('release_date')
        lyrics = request.form.get('lyrics')
        selected_album_id = request.form.get('album')
        release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
        new_song = Song(
            title=title,
            artist=artist,
            release_date=release_date,
            lyrics=lyrics,
            user_id=user.id,
            album_id=selected_album_id
        )
        db.session.add(new_song)
        db.session.commit()
        return redirect(url_for('dashboard', username=user.username))

    return render_template('upload_a_song.html', user=user, albums=albums)

@app.route('/create_album/<string:username>', methods=['GET', 'POST'])
def create_album(username):
    user = User.query.filter_by(username=username).first()

    if request.method == 'POST':
        name = request.form.get('name')
        genre = request.form.get('genre')
        artist = request.form.get('artist')

        if user:
            new_album = Album(
                name=name,
                genre=genre,
                artist=artist,
                user_id=user.id
            )

            db.session.add(new_album)
            db.session.commit()
            return redirect(url_for('dashboard', username=user.username))

    return render_template('create_album.html', user=user)

@app.route('/play_song/<int:song_id>/<string:username>', methods=['GET'])
def play_song(song_id,username):
    user = User.query.filter_by(username=username).first()
    song = Song.query.get(song_id)
    comments = Comment.query.filter_by(song_id=song_id).all()
    if song:
        return render_template('play_song.html', song=song, comments=comments, user=user)

@app.route('/submit_comment/<int:song_id>/<string:username>', methods=['POST'])
def submit_comment(song_id,username):
    if request.method == 'POST':
        comment_text = request.form.get('comment')
        rating_value = request.form.get('rating')
        user = User.query.filter_by(username=username).first()
        song = Song.query.get(song_id)
        new_comment = Comment(
            text=comment_text,
            value=rating_value,
            timestamp=datetime.utcnow(),
            user_id=user.id,
            song_id=song_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('play_song', song_id=song_id , username=user.username ))


@app.route('/dashboard/<string:username>', methods=['GET', 'POST'])
def dashboard(username):
    user = User.query.filter_by(username=username).first()
    if user:
        song_search_query = request.args.get('song_search', '')
        playlist_search_query = request.args.get('playlist_search', '')
        if song_search_query:
            songs = Song.query.filter(Song.title==song_search_query).all()
        else:
            songs=Song.query.all()
        playlists_query = Playlist.query.filter(Playlist.user_id == user.id)
        if playlist_search_query:
            playlists = playlists_query.filter(Playlist.name==playlist_search_query).all()
        else:
            playlists = playlists_query.all()
     
        genres_query = db.session.query(Album.genre).distinct()
        genres = [genre[0] for genre in genres_query]

        genres_with_songs = {}

        for genre in genres:
            albums = Album.query.filter_by(genre=genre).all()
            
            for album in albums:
                genre_songs = Song.query.filter_by(album_id=album.id).all()
                
                if genre_songs:
                    if genre in genres_with_songs:
                        genres_with_songs[genre].extend(genre_songs)
                    else:
                        genres_with_songs[genre] = genre_songs
        genres_with_songs_list = list(genres_with_songs.items())
        if user.role == "creator":
            return render_template('creator_dashboard.html', user=user, all_songs=songs, playlists=playlists, genres_with_songs_list=genres_with_songs_list, song_search_query=song_search_query, playlist_search_query=playlist_search_query)
        else:
            return render_template('user_dashboard.html', user=user, all_songs=songs, playlists=playlists, genres_with_songs_list=genres_with_songs_list, song_search_query=song_search_query, playlist_search_query=playlist_search_query)


@app.route('/confirmation_page/<string:username>')
def confirmation_page(username):
    user = User.query.filter_by(username=username).first()

    if user and request.args.get('confirm') == 'true':
        user.role = 'creator'
        db.session.commit()
        return redirect(url_for('dashboard', username=username))
    elif user:
        return render_template('register_as_creator.html', user=user)
    
@app.route('/create_playlist/<string:username>', methods=['GET', 'POST'])
def create_playlist(username):
    user = User.query.filter_by(username=username).first()

    if user:
        if request.method == 'POST':
            playlist_name = request.form.get('playlist_name')
            selected_song_ids = request.form.getlist('selected_songs')
            new_playlist = Playlist(name=playlist_name, user_id=user.id)
            db.session.add(new_playlist)
            db.session.commit()
            for song_id in selected_song_ids:
                song = Song.query.get(song_id)
                if song:
                    new_playlist.songs.append(song)
            db.session.commit()
            return redirect(url_for('dashboard', username=username))
        all_songs = Song.query.all()

        return render_template('create_playlist.html', user=user, all_songs=all_songs)

    return render_template('login.html', message={'type': 'danger', 'text': 'User not found.'})

@app.route('/playlist/<int:playlist_id>/<string:username>')
def playlist_detail(playlist_id, username):
    user = User.query.filter_by(username=username).first()
    playlist = Playlist.query.get(playlist_id)
    all_songs = Song.query.all()
    if playlist:
        return render_template('playlist_details.html', playlist=playlist,all_songs=all_songs,user=user)


@app.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
def delete_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    user=playlist.user.username
    if playlist:
        db.session.delete(playlist)
        db.session.commit()
    return redirect(url_for('dashboard', username=user))

@app.route('/remove_song_from_playlist/<int:playlist_id>/<int:song_id>', methods=['POST'])
def remove_song_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get(playlist_id)
    user=playlist.user.username
    song = Song.query.get(song_id)

    if playlist and song:
        playlist.songs.remove(song)
        db.session.commit()

    return redirect(url_for('playlist_detail', playlist_id=playlist_id,username=user))


@app.route('/update_playlist_name/<int:playlist_id>', methods=['POST'])
def update_playlist_name(playlist_id):
    new_playlist_name = request.form.get('new_playlist_name')
    playlist = Playlist.query.get(playlist_id)
    user=playlist.user.username
    if playlist and new_playlist_name:
        playlist.name = new_playlist_name
        db.session.commit()

    return redirect(url_for('playlist_detail', playlist_id=playlist_id,username=user))

@app.route('/add_song_to_playlist/<int:playlist_id>', methods=['POST'])
def add_song_to_playlist(playlist_id):
    song_id = request.form.get('song_id')
    playlist = Playlist.query.get(playlist_id)
    user=playlist.user.username
    song = Song.query.get(song_id)

    if playlist and song:
        playlist.songs.append(song)
        db.session.commit()

    return redirect(url_for('playlist_detail', playlist_id=playlist_id,username=user))


@app.route('/logout')
def logout():
    return redirect(url_for('index'))





class NotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response("", status_code)

class Course_name_error(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)

parser = reqparse.RequestParser()
parser.add_argument("title")
parser.add_argument("artist")
parser.add_argument("lyrics")
parser.add_argument("release_date")
parser.add_argument("user_id")
parser.add_argument("album_id")
parser.add_argument("name")
parser.add_argument("genre")

class SongApi(Resource):
    def get(self, id):
        try:
            entry = Song.query.get(id)
            if not entry:
                raise NotFoundError(status_code=404)
                
            return {
                "song_id": entry.id,
                "title": entry.title,
                "artist": entry.artist,
                "lyrics": entry.lyrics,
                "release_date": str(entry.release_date)
            }
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self):
        try:
            args = parser.parse_args()
            required_fields = ["title", "artist", "lyrics", "release_date", "user_id", "album_id"]
            
            for field in required_fields:
                if not args.get(field):
                    raise Course_name_error(
                        status_code=400,
                        error_code="SONG_ERROR",
                        error_message=f"Missing required field: {field}"
                    )
            
            release_date = datetime.strptime(args["release_date"], "%Y-%m-%d").date()
            
            if Song.query.filter_by(title=args["title"]).first():
                return {"error": "Song already exists"}, 409

            new_song = Song(
                title=args["title"],
                artist=args["artist"],
                lyrics=args["lyrics"],
                release_date=release_date,
                user_id=args["user_id"],
                album_id=args["album_id"]
            )
            
            db.session.add(new_song)
            db.session.commit()
            
            return {
                "song_id": new_song.id,
                "title": new_song.title,
                "artist": new_song.artist,
                "lyrics": new_song.lyrics,
                "release_date": str(new_song.release_date)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            entry = Song.query.get(id)
            if not entry:
                raise NotFoundError(status_code=404)

            args = parser.parse_args()
            required_fields = ["title", "artist", "lyrics", "release_date"]
            
            for field in required_fields:
                if not args.get(field):
                    raise Course_name_error(
                        status_code=400,
                        error_code="SONG_ERROR",
                        error_message=f"Missing required field: {field}"
                    )

            entry.title = args["title"]
            entry.artist = args["artist"]
            entry.lyrics = args["lyrics"]
            entry.release_date = datetime.strptime(args["release_date"], "%Y-%m-%d").date()
            
            db.session.commit()
            
            return {
                "song_id": entry.id,
                "title": entry.title,
                "artist": entry.artist,
                "lyrics": entry.lyrics,
                "release_date": str(entry.release_date)
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, id):
        try:
            entry = Song.query.get(id)
            if not entry:
                raise NotFoundError(status_code=404)
                
            db.session.delete(entry)
            db.session.commit()
            return {"message": "Successfully Deleted"}, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class AlbumApi(Resource):
    def get(self, id):
        try:
            entry = Album.query.get(id)
            if not entry:
                raise NotFoundError(status_code=404)
                
            return {
                "album_id": entry.id,
                "name": entry.name,
                "genre": entry.genre,
                "artist": entry.artist
            }
        except Exception as e:
            return {"error": str(e)}, 500

    def post(self):
        try:
            args = parser.parse_args()
            required_fields = ["name", "genre", "artist", "user_id"]
            
            for field in required_fields:
                if not args.get(field):
                    raise Course_name_error(
                        status_code=400,
                        error_code="ALBUM_ERROR",
                        error_message=f"Missing required field: {field}"
                    )
            
            if Album.query.filter_by(name=args["name"]).first():
                return {"error": "Album already exists"}, 409

            new_album = Album(
                name=args["name"],
                genre=args["genre"],
                artist=args["artist"],
                user_id=args["user_id"]
            )
            
            db.session.add(new_album)
            db.session.commit()
            
            return {
                "album_id": new_album.id,
                "name": new_album.name,
                "genre": new_album.genre,
                "artist": new_album.artist
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def put(self, id):
        try:
            entry = Album.query.get(id)
            if not entry:
                raise NotFoundError(status_code=404)

            args = parser.parse_args()
            required_fields = ["name", "genre", "artist"]
            
            for field in required_fields:
                if not args.get(field):
                    raise Course_name_error(
                        status_code=400,
                        error_code="ALBUM_ERROR",
                        error_message=f"Missing required field: {field}"
                    )

            entry.name = args["name"]
            entry.genre = args["genre"]
            entry.artist = args["artist"]
            
            db.session.commit()
            
            return {
                "album_id": entry.id,
                "name": entry.name,
                "genre": entry.genre,
                "artist": entry.artist
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, id):
        try:
            entry = Album.query.get(id)
            if not entry:
                raise NotFoundError(status_code=404)
                
            db.session.delete(entry)
            db.session.commit()
            return {"message": "Successfully Deleted"}, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

# Initialize API resources
api.add_resource(SongApi, "/api/song/<int:id>", "/api/song")
api.add_resource(AlbumApi, "/api/album/<int:id>", "/api/album")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)