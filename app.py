from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from schema.init_script import reinitializeDatabase, initEnvironment

from middleware.keyGen import generateKey
from middleware.tokenGenerator import generateToken
from middleware.tokenValidator import validateToken
import sqlite3

import os

from datetime import datetime

# from PIL import Image

app = Flask(__name__)
app.secret_key = "OkvzD0IvqdPOa47J0q3z5VaGy2cCDoP6V5GEfO0kGeq3vFfk1cb7vs8QMJiwF0nGIcXWCKoqD6wE6h1mUQZdQu7hR3FLjDwyRCCOY6bfuLBpr+WgQIDAQABAoGAENt4zTvrXc7Sig4N3tUsJ"

app.config["UPLOAD_FOLDER"] = "static"

# /
@app.route("/", methods=["GET"])
def homeScreen():
    return render_template("home.html")

# /auth
@app.route("/auth/login", methods=["GET", "POST"])
def loginScreen():
    if request.method == "POST":
        # print(request.form.get('userEmail'))
        # print(request.form.get('userPassword'))
        userEmail = request.form.get("userEmail")
        userPassword = request.form.get("userPassword")

        if len(str(userEmail)) == 0 or len(str(userPassword)) == 0:
            flash("Please fill all the fields", "danger")
            return redirect(url_for("loginScreen"))

        try:
            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()
            db_cursor.execute(
                f"SELECT * FROM userData WHERE userEmail = ? AND userPassword = ? AND (userRoleId = 1 OR userRoleId = 2)",
                (userEmail, userPassword),
            )
            userData = db_cursor.fetchone()
            db_connection.close()

            if userData is None:
                flash("Invalid credentials", "danger")
                return redirect(url_for("loginScreen"))
            else:
                secretToken = generateToken(
                    {
                        "userId": userData[0],
                        "userName": userData[1],
                        "userEmail": userData[2],
                        "userRoleId": userData[4],
                    }
                )

                if secretToken == -1:
                    flash("Something went wrong", "danger")
                    return redirect(url_for("loginScreen"))

                session["secretToken"] = secretToken
                session["userId"] = userData[0]
                session["userName"] = userData[1]
                session["userEmail"] = userData[2]
                session["userRoleId"] = userData[4]

                if userData[4] == 1:
                    return redirect(url_for("userDashboardScreen"))
                elif userData[4] == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                else:
                    flash("Invalid user role", "danger")
                    return redirect(url_for("loginScreen"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something went wrong", "danger")
            return redirect(url_for("loginScreen"))

    elif request.method == "GET":
        return render_template("auth/login.html")


@app.route("/auth/adminLogin", methods=["GET", "POST"])
def adminLoginScreen():
    if request.method == "POST":
        adminEmail = request.form.get("adminEmail")
        adminPassword = request.form.get("adminPassword")

        if len(adminEmail) == 0 or len(adminPassword) == 0:
            flash("Please fill all the fields", "danger")
            return redirect(url_for("adminLoginScreen"))

        try:
            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()
            db_cursor.execute(
                f"SELECT * FROM userData WHERE userEmail = ? AND userPassword = ? AND userRoleId = '0'",
                (adminEmail, adminPassword),
            )
            adminData = db_cursor.fetchone()
            db_connection.close()

            if adminData is None:
                flash("Invalid credentials", "danger")
                return redirect(url_for("adminLoginScreen"))
            else:
                secretToken = generateToken(
                    {
                        "userId": adminData[0],
                        "userName": adminData[1],
                        "userEmail": adminData[2],
                        "userRoleId": adminData[4],
                    }
                )

                if secretToken == -1:
                    flash("Something went wrong", "danger")
                    return redirect(url_for("adminLoginScreen"))

                session["secretToken"] = secretToken
                session["userId"] = adminData[0]
                session["userName"] = adminData[1]
                session["userEmail"] = adminData[2]
                session["userRoleId"] = adminData[4]

                return redirect(url_for("adminDashboard"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something went wrong", "danger")
            return redirect(url_for("adminLoginScreen"))

    elif request.method == "GET":
        return render_template("auth/admin_login.html")


@app.route("/auth/register", methods=["GET", "POST"])
def registerScreen():
    if request.method == "POST":
        userEmail = request.form.get("userEmail")
        userPassword = request.form.get("userPassword")
        userName = request.form.get("userName")
        userDob = request.form.get("userDob")
        userGender = request.form.get("userGender")

        if (
            len(str(userEmail)) == 0
            or len(str(userPassword)) == 0
            or len(str(userName)) == 0
            or len(str(userDob)) == 0
            or len(str(userGender)) == 0
        ):
            flash("Please fill all the fields", "danger")
            return redirect(url_for("registerScreen"))

        # Check DOB format (YYYY-MM-DD)
        if (
            len(userDob.split("-")) != 3
            and len(userDob.split("-")[0]) != 4
            and len(userDob.split("-")[1]) != 2
            and len(userDob.split("-")[2]) != 2
        ):
            flash("Invalid DOB format", "danger")
            return redirect(url_for("registerScreen"))

        try:
            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if user already exists
            db_cursor.execute(
                f"SELECT * FROM userData WHERE userEmail = ?", (userEmail,)
            )
            userData = db_cursor.fetchone()

            if userData is not None:
                flash("User already exists", "danger")
                return redirect(url_for("registerScreen"))

            # Insert user data
            db_cursor.execute(
                f"INSERT INTO userData (userName, userEmail, userPassword, userDob, userGender, userRoleId, accountStatus) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (userName, userEmail, userPassword, userDob, userGender, 1, "1"),
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("registerScreen"))

            db_connection.commit()
            db_connection.close()

            flash("User created successfully", "success")
            return redirect(url_for("loginScreen"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something went wrong", "danger")
            return redirect(url_for("registerScreen"))

    elif request.method == "GET":
        return render_template("auth/register.html")


@app.route("/auth/logout", methods=["GET"])
def logoutScreen():
    try:
        session.clear()
        return redirect(url_for("loginScreen"))
    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something went wrong", "danger")
        return redirect(url_for("loginScreen"))


# /admin
@app.route("/admin/dashboard", methods=["GET"])
def adminDashboard():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if userRoleId != 0:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("adminLoginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("adminLoginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("adminLoginScreen"))
        
        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get total CREATOR count
        db_cursor.execute(f"SELECT COUNT(*) FROM userData WHERE userRoleId = 2")
        creatorCount = db_cursor.fetchone()[0]

        # Get total USER count
        db_cursor.execute(f"SELECT COUNT(*) FROM userData WHERE userRoleId = 1")
        userCount = db_cursor.fetchone()[0]

        # Get total SONG count
        db_cursor.execute(f"SELECT COUNT(*) FROM songData")
        songCount = db_cursor.fetchone()[0]

        # Get total ALBUM count
        db_cursor.execute(f"SELECT COUNT(*) FROM albumData")
        albumCount = db_cursor.fetchone()[0]

        # Get total GENRE count
        db_cursor.execute(f"SELECT COUNT(*) FROM genreData")
        genreCount = db_cursor.fetchone()[0]

        # Get total LANGUAGE count
        db_cursor.execute(f"SELECT COUNT(*) FROM languageData")
        languageCount = db_cursor.fetchone()[0]

        # Get total PLAYLIST count
        db_cursor.execute(f"SELECT COUNT(*) FROM playlistData")
        playlistCount = db_cursor.fetchone()[0]

        db_connection.close()

        return render_template(
            "admin/admin_dashboard.html",
            creatorCount=creatorCount,
            userCount=userCount,
            songCount=songCount,
            albumCount=albumCount,
            genreCount=genreCount,
            languageCount=languageCount,
            playlistCount=playlistCount,
        )


    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("adminLoginScreen"))


# /user
@app.route("/user/dashboard", methods=["GET"])
def userDashboardScreen():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        # print(session, "Here")

        if userRoleId != 1:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))

    return render_template("user/user_dashboard.html")


@app.route("/user/registerAsCreator", methods=["POST"])
def registerAsCreator():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if userRoleId != 1 and userRoleId != 2:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user is currently a user
        db_cursor.execute(
            f"SELECT * FROM userData WHERE userId = ? AND userRoleId = 1", (userId,)
        )
        userData = db_cursor.fetchone()

        if userData is None:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("userDashboardScreen"))

        # Check if user already exists as creator
        db_cursor.execute(
            f"SELECT * FROM userData WHERE userId = ? AND userRoleId = 2", (userId,)
        )
        userData = db_cursor.fetchone()

        if userData is not None:
            flash("User already exists as creator", "danger")
            return redirect(url_for("userDashboardScreen"))

        db_cursor.execute(
            f"UPDATE userData SET userRoleId = 2 WHERE userId = ?", (userId,)
        )

        affectedRows = db_cursor.rowcount
        if affectedRows == 0:
            flash("Something went wrong", "danger")
            return redirect(url_for("userDashboardScreen"))

        db_connection.commit()
        db_connection.close()

        session["userRoleId"] = 2

        return {"message": "Registered as creator successfully"}

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("userDashboardScreen"))


@app.route("/creator/dashboard", methods=["GET"])
def creatorDashboardScreen():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if userRoleId != 2:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get all songs
        db_cursor.execute(
            f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.createdBy = ? ORDER BY s.createdAt DESC LIMIT 10",
            (userId,),
        )

        # Get Song Count
        songList = db_cursor.fetchall()

        if songList is None:
            songList = []

        songCount = len(songList)

        # Album Count
        db_cursor.execute(
            f"SELECT COUNT(*) FROM albumData WHERE createdBy = ?", (userId,)
        )
        albumCount = db_cursor.fetchone()[0]

        db_connection.close()

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))

    return render_template(
        "creator/creator_dashboard.html",
        songList=songList,
        songCount=songCount,
        albumCount=albumCount,
    )


# /song
@app.route("/song", methods=["GET"])
def songListScreen():
    # try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]
        searchQuery = request.args.get("search")
        genreQuery = request.args.get("songGenre")
        languageQuery = request.args.get("songLanuage")

        if searchQuery is None:
            searchQuery = ""

        if genreQuery is None:
            genreQuery = ""

        if languageQuery is None:
            languageQuery = ""

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        print(f"{searchQuery}, {genreQuery}, {languageQuery}")

        if userRoleId == 2:
            # Get all songs
            db_cursor.execute(
                f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.createdBy = ? AND s.songName LIKE ? ORDER BY s.createdAt DESC",
                (userId, f"%{searchQuery}%"),
            )
        elif userRoleId == 1:
            # Get all songs
            if genreQuery != "" and languageQuery != "":
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND g.genreId = ? AND l.languageId = ? AND s.isActive = '1' ORDER BY s.createdAt DESC",
                    (
                        f"%{searchQuery}%",
                        genreQuery,
                        languageQuery,
                    ),
                )
            elif genreQuery != "" and languageQuery == "":
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND g.genreId = ? AND s.isActive = '1' ORDER BY s.createdAt DESC",
                    (
                        f"%{searchQuery}%",
                        genreQuery,
                    ),
                )
            elif genreQuery == "" and languageQuery != "":
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND l.languageId = ? AND s.isActive = '1' ORDER BY s.createdAt DESC",
                    (
                        f"%{searchQuery}%",
                        languageQuery,
                    ),
                )
            else:
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND s.isActive = '1' ORDER BY s.createdAt DESC",
                    (f"%{searchQuery}%",),
                )

        elif userRoleId == 0:
            if genreQuery != "" and languageQuery != "":
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND g.genreId = ? AND l.languageId = ? ORDER BY s.createdAt DESC",
                    (
                        f"%{searchQuery}%",
                        genreQuery,
                        languageQuery,
                    ),
                )
            elif genreQuery != "" and languageQuery == "":
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND g.genreId = ? ORDER BY s.createdAt DESC",
                    (
                        f"%{searchQuery}%",
                        genreQuery,
                    ),
                )
            elif genreQuery == "" and languageQuery != "":
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? AND l.languageId = ? ORDER BY s.createdAt DESC",
                    (
                        f"%{searchQuery}%",
                        languageQuery,
                    ),
                )
            else:
                db_cursor.execute(
                    f"SELECT s.songId, s.songName, g.genreName, s.songLyrics, s.audioFileExt, s.imageFileExt, s.isActive, s.likesCount FROM songData AS s JOIN genreData AS g ON g.genreId = s.songGenreId JOIN languageData AS l ON l.languageId = s.songLanguageId WHERE s.songName LIKE ? ORDER BY s.createdAt DESC",
                    (f"%{searchQuery}%",),
                )

        # Get Song Count
        songList = db_cursor.fetchall()

        if songList is None:
            songList = []

        songCount = len(songList)

        # Liked Songs
        db_cursor.execute(
            "SELECT songId, isLike FROM songLikes WHERE userId = ?", (userId,)
        )
        likedSongData = db_cursor.fetchall()
        if likedSongData is None:
            likedSongData = []

        likedSongs = []
        unLikedSongs = []
        for song in likedSongData:
            if song[1] == '1':
                likedSongs.append(song[0])
            elif song[1] == '0':
                unLikedSongs.append(song[0])

        for i in range(len(songList)):
            if songList[i][0] in likedSongs:
                songList[i] = list(songList[i])
                songList[i].append(True)
            elif songList[i][0] in unLikedSongs:
                songList[i] = list(songList[i])
                songList[i].append(False)
            else:
                songList[i] = list(songList[i])
                songList[i].append(None)

        # dislikedSongIds Count
        db_cursor.execute(
            "SELECT songId, COUNT(*) FROM songLikes WHERE isLike = '0' GROUP BY songId"
        )
        dislikedSongIds = db_cursor.fetchall()
        if dislikedSongIds is None:
            dislikedSongIds = []

        for i in range(len(songList)):
            flag = False
            for j in range(len(dislikedSongIds)):
                if songList[i][0] == dislikedSongIds[j][0]:
                    songList[i] = list(songList[i])
                    songList[i].append(dislikedSongIds[j][1])
                    flag = True
                    break
            if flag == False:
                songList[i] = list(songList[i])
                songList[i].append(0)
            
            print(songList[i][5:])

        # Get all genres
        db_cursor.execute(f"SELECT * FROM genreData")
        genreList = db_cursor.fetchall()

        # Get all languages
        db_cursor.execute(f"SELECT * FROM languageData")
        languageList = db_cursor.fetchall()

        db_connection.close()

        if userRoleId == 2:
            return render_template(
                "creator/song_list.html",
                songList=songList,
                genreList=genreList,
                languageList=languageList,
                songCount=songCount,
                searchQuery=searchQuery,
            )

        elif userRoleId == 0:
            return render_template(
                "admin/song_list.html",
                songList=songList,
                genreList=genreList,
                languageList=languageList,
                songCount=songCount,
                searchQuery=searchQuery,
                songGenre=int(genreQuery) if genreQuery != "" else "",
                songLanguage=int(languageQuery) if languageQuery != "" else "",
            )

        elif userRoleId == 1:
            return render_template(
                "user/song_list.html",
                songList=songList,
                genreList=genreList,
                languageList=languageList,
                searchQuery=searchQuery,
                songGenre=int(genreQuery) if genreQuery != "" else "",
                songLanguage=int(languageQuery) if languageQuery != "" else "",
            )

        else:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

    # except Exception as e:
    #     print(e)
    #     f = open("logs/errorLogs.txt", "a")
    #     f.write(f"[ERROR] {datetime.now()}: {e}\n")
    #     f.close()

    #     flash("Something Went Wrong.\nPlease try again later.", "danger")
    #     return redirect(url_for("loginScreen"))


@app.route("/song/new", methods=["GET", "POST"])
def addNewSong():
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get all genres
            db_cursor.execute(f"SELECT * FROM genreData")
            genreList = db_cursor.fetchall()

            db_cursor.execute(f"SELECT * FROM languageData")
            languageList = db_cursor.fetchall()

            db_connection.close()

            if genreList is None:
                flash(
                    "No Genres found to add new songs! Add new Genres to continue",
                    "danger",
                )
                return redirect(url_for("addNewGenre"))

            if userRoleId == 2:
                return render_template(
                    "creator/new_song.html",
                    genreList=genreList,
                    languageList=languageList,
                )
            elif userRoleId == 0:
                return render_template(
                    "admin/new_song.html",
                    genreList=genreList,
                    languageList=languageList,
                )

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            songName = request.form.get("songName")
            songDescription = request.form.get("songDescription")
            songGenre = request.form.get("songGenre")
            songLanguage = request.form.get("songLanguage")
            songLyrics = request.form.get("songLyrics")
            songReleaseDate = request.form.get("songReleaseDate")
            songAudio = request.files["songAudio"]
            songCover = request.files["songCover"]

            print(
                {
                    "songName": songName,
                    "songDescription": songDescription,
                    "songGenre": songGenre,
                    "songLanguage": songLanguage,
                    "songLyrics": songLyrics,
                    "songReleaseDate": songReleaseDate,
                    "songAudio": songAudio.filename,
                    "songCover": songCover.filename,
                }
            )

            print(songAudio.filename.split(".")[1])
            print(songCover.filename.split(".")[1])

            # INSERT DATA AND IF SUCCESSFUL, UPLOAD FILES
            if (
                len(str(songName)) == 0
                or len(str(songDescription)) == 0
                or len(str(songGenre)) == 0
                or len(str(songLanguage)) == 0
                or len(str(songLyrics)) == 0
                or len(str(songReleaseDate)) == 0
            ):
                flash("Please fill all the fields", "danger")
                return redirect(url_for("addNewSong"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if song already exists
            db_cursor.execute(f"SELECT * FROM songData WHERE songName = ?", (songName,))
            songData = db_cursor.fetchone()

            if songData is not None:
                flash("Song already exists", "danger")
                return redirect(url_for("addNewSong"))

            # TODO: SongDuration
            # Insert song data
            db_cursor.execute(
                f"INSERT INTO songData (songName, songDescription, songLyrics, songReleaseDate, songGenreId, songLanguageId, isActive, createdBy, audioFileExt, imageFileExt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    songName,
                    songDescription,
                    songLyrics,
                    songReleaseDate,
                    songGenre,
                    songLanguage,
                    "1",
                    userId,
                    songAudio.filename.split(".")[-1],
                    songCover.filename.split(".")[-1],
                ),
            )

            affectedRows = db_cursor.rowcount
            songId = db_cursor.lastrowid

            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewSong"))

            # Upload song audio
            songAudio.save(
                f"static/music/song/{songId}.{songAudio.filename.split('.')[-1]}"
            )

            # Upload song cover
            songCover.save(
                f"static/music/poster/{songId}.{songCover.filename.split('.')[-1]}"
            )

            db_connection.commit()
            db_connection.close()

            if userRoleId == 2:
                return redirect(url_for("creatorDashboardScreen"))
            elif userRoleId == 0:
                return redirect(url_for("adminDashboard"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/song/<songId>/edit", methods=["GET", "POST"])
def editSong(songId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            songId = songData[0]
            songName = songData[1]
            songDescription = songData[2]
            songLyrics = songData[4]
            songReleaseDate = songData[6]
            songGenre = songData[7]
            songLanguage = songData[9]
            createdBy = songData[12]
            songAudioExt = songData[16]
            songCoverExt = songData[17]

            # Check if user is creator of the song
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            # Get all genres
            db_cursor.execute(f"SELECT * FROM genreData")
            genreList = db_cursor.fetchall()

            db_cursor.execute(f"SELECT * FROM languageData")
            languageList = db_cursor.fetchall()

            db_connection.close()

            if genreList is None:
                flash(
                    "No Genres found to add new songs! Add new Genres to continue",
                    "danger",
                )
                return redirect(url_for("addNewGenre"))

            if userRoleId == 2:
                return render_template(
                    "creator/edit_song.html",
                    songId=songId,
                    songName=songName,
                    songDescription=songDescription,
                    songLyrics=songLyrics,
                    songReleaseDate=songReleaseDate,
                    songGenre=songGenre,
                    songLanguage=songLanguage,
                    genreList=genreList,
                    languageList=languageList,
                    songAudioExt=songAudioExt,
                    songCoverExt=songCoverExt,
                )
            elif userRoleId == 0:
                return render_template(
                    "admin/edit_song.html",
                    songId=songId,
                    songName=songName,
                    songDescription=songDescription,
                    songLyrics=songLyrics,
                    songReleaseDate=songReleaseDate,
                    songGenre=songGenre,
                    songLanguage=songLanguage,
                    genreList=genreList,
                    languageList=languageList,
                    songAudioExt=songAudioExt,
                    songCoverExt=songCoverExt,
                )

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    # POST
    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            songName = request.form.get("songName")
            songDescription = request.form.get("songDescription")
            songGenre = request.form.get("songGenre")
            songLanguage = request.form.get("songLanguage")
            songLyrics = request.form.get("songLyrics")
            songReleaseDate = request.form.get("songReleaseDate")
            songAudio = request.files["songAudio"]
            songCover = request.files["songCover"]

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            songId = songData[0]
            originalSongName = songData[1]
            songDescription = songData[2]
            songLyrics = songData[4]
            songReleaseDate = songData[6]
            songGenre = songData[7]
            songLanguage = songData[9]
            createdBy = songData[12]
            songAudioExt = songData[16]
            songCoverExt = songData[17]

            # Check if user is creator of the song
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            # INSERT DATA AND IF SUCCESSFUL, UPLOAD FILES
            if (
                len(str(songName)) == 0
                or len(str(songDescription)) == 0
                or len(str(songGenre)) == 0
                or len(str(songLanguage)) == 0
                or len(str(songLyrics)) == 0
                or len(str(songReleaseDate)) == 0
            ):
                flash("Please fill all the fields", "danger")
                return redirect(url_for("addNewSong"))

            if originalSongName != songName:
                # Check if song already exists
                db_cursor.execute(
                    f"SELECT * FROM songData WHERE songName = ?", (songName,)
                )
                songData = db_cursor.fetchone()

                if songData is not None:
                    flash("Song already exists", "danger")
                    return redirect(url_for("addNewSong"))

            db_cursor.execute(
                f"UPDATE songData SET songName = ?, songDescription = ?, songLyrics = ?, songReleaseDate = ?, songGenreId = ?, songLanguageId = ? WHERE songId = ?",
                (
                    songName,
                    songDescription,
                    songLyrics,
                    songReleaseDate,
                    songGenre,
                    songLanguage,
                    songId,
                ),
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewSong"))

            # Upload song audio
            if songAudio.filename != "":
                db_cursor.execute(
                    f"UPDATE songData SET audioFileExt = ? WHERE songId = ?",
                    (songAudio.filename.split(".")[-1], songId),
                )
                # Remove old file
                os.remove(f"static/music/song/{songId}.{songAudioExt}")
                # Upload new file
                songAudio.save(
                    f"static/music/song/{songId}.{songAudio.filename.split('.')[-1]}"
                )

            # Upload song cover
            if songCover.filename != "":
                db_cursor.execute(
                    f"UPDATE songData SET imageFileExt = ? WHERE songId = ?",
                    (songCover.filename.split(".")[-1], songId),
                )
                # Remove old file
                os.remove(f"static/music/poster/{songId}.{songCoverExt}")
                # Upload new file
                songCover.save(
                    f"static/music/poster/{songId}.{songCover.filename.split('.')[-1]}"
                )

            db_connection.commit()
            db_connection.close()

            if userRoleId == 2:
                return redirect(url_for("creatorDashboardScreen"))
            elif userRoleId == 0:
                return redirect(url_for("adminDashboard"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

@app.route("/song/<songId>/like", methods=["GET"])
def likeSong(songId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if user has already liked the song
            db_cursor.execute(
                f"SELECT * FROM songLikes WHERE songId = ? AND userId = ?",
                (songId, userId),
            )
            songLikeData = db_cursor.fetchone()

            if songLikeData is None:
                db_cursor.execute(
                    f"INSERT INTO songLikes (songId, userId, isLike) VALUES (?, ?, '1')",
                    (songId, userId),
                )
                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return {"message": "Something went wrong"}

                db_cursor.execute(
                    f"UPDATE songData SET likesCount = likesCount + 1 WHERE songId = ?",
                    (songId,),
                )

                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("songListScreen"))
                
            else:
                if songLikeData[2] == '1':
                    flash("Already Liked", "danger")
                    return redirect(url_for("songListScreen"))
                
                db_cursor.execute(
                    f"UPDATE songLikes SET isLike = '1' WHERE songId = ? AND userId = ?",
                    (songId, userId),
                )
                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("loginScreen"))
                
                db_cursor.execute(
                    f"UPDATE songData SET likesCount = likesCount + 1 WHERE songId = ?",
                    (songId,),
                )

                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("songListScreen"))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("songListScreen"))

        except Exception as e:
            print(e)
            return {"message": "Something Went Wrong.\nPlease try again later."}
        
@app.route("/song/<songId>/unlike", methods=["GET"])
def unlikeSong(songId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))
            
            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                return redirect(url_for("loginScreen"))
            
            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2]
            )

            if decryptedToken == -2:
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                return redirect(url_for("loginScreen"))
            
            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if user has already liked the song
            db_cursor.execute(
                f"SELECT * FROM songLikes WHERE songId = ? AND userId = ?",
                (songId, userId)
            )

            songLikeData = db_cursor.fetchone()

            if songLikeData is None:
                db_cursor.execute(
                    f"INSERT INTO songLikes (songId, userId, isLike) VALUES (?, ?, '0')",
                    (songId, userId)
                )
                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("songListScreen"))
                
                db_cursor.execute(
                    f"UPDATE songData SET likesCount = likesCount - 1 WHERE songId = ?",
                    (songId,)
                )

                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("songListScreen"))
                
            else:
                if songLikeData[2] == '0':
                    flash("Already Unliked", "danger")
                    return redirect(url_for("songListScreen"))
                db_cursor.execute(
                    f"UPDATE songLikes SET isLike = '0' WHERE songId = ? AND userId = ?",
                    (songId, userId)
                )
                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("songListScreen"))
                
                db_cursor.execute(
                    f"UPDATE songData SET likesCount = likesCount - 1 WHERE songId = ?",
                    (songId,)
                )

                affectedRows = db_cursor.rowcount
                if affectedRows == 0:
                    return redirect(url_for("songListScreen"))
                
            db_connection.commit()
            db_connection.close()

            return redirect(url_for("songListScreen"))

        except Exception as e:
            print(e)
            return {"message": "Something Went Wrong.\nPlease try again later."}

@app.route("/song/<songId>/deactivate", methods=["GET"])
def deactivateSong(songId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            songId = songData[0]
            createdBy = songData[12]

            # Check if user is creator of the song
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_cursor.execute(
                f"UPDATE songData SET isActive = '0' WHERE songId = ?", (songId,)
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewSong"))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("songListScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/song/<songId>/activate", methods=["GET"])
def activateSong(songId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            songId = songData[0]
            createdBy = songData[12]

            # Check if user is creator of the song
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_cursor.execute(
                f"UPDATE songData SET isActive = '1' WHERE songId = ?", (songId,)
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewSong"))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("songListScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


# /language
@app.route("/language", methods=["GET"])
def languageScreen():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if userRoleId != 2 and userRoleId != 0:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get all languages
        db_cursor.execute(f"SELECT * FROM languageData ORDER BY languageName")

        languageList = db_cursor.fetchall()

        db_connection.close()

        if languageList is None:
            languageList = []

        if userRoleId == 2:
            return render_template("creator/language.html", languageList=languageList)

        elif userRoleId == 0:
            return render_template("admin/language.html", languageList=languageList)

        else:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/language/new", methods=["GET", "POST"])
def addNewLanguage():
    if request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            languageName = request.form.get("languageName")

            if len(str(languageName)) == 0:
                flash("Please fill all the fields", "danger")
                return redirect(url_for("addNewLanguage"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if language already exists
            db_cursor.execute(
                f"SELECT * FROM languageData WHERE languageName = ?", (languageName,)
            )
            languageData = db_cursor.fetchone()

            if languageData is not None:
                flash("Language already exists", "danger")
                return redirect(url_for("addNewLanguage"))

            db_cursor.execute(
                f"INSERT INTO languageData (languageName) VALUES (?)", (languageName,)
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewLanguage"))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("languageScreen"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    elif request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            return render_template("creator/new_language.html")

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/language/<languageId>/edit", methods=["GET", "POST"])
def editLanguage(languageId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get language data
            db_cursor.execute(
                f"SELECT * FROM languageData WHERE languageId = ?", (languageId,)
            )
            languageData = db_cursor.fetchone()

            if languageData is None:
                flash("Language not found", "danger")
                return redirect(url_for("languageScreen"))

            languageId = languageData[0]
            languageName = languageData[1]

            db_connection.close()

            return render_template(
                "creator/edit_language.html",
                languageId=languageId,
                languageName=languageName,
            )

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            languageName = request.form.get("languageName")

            if len(str(languageName)) == 0:
                flash("Please fill all the fields", "danger")
                return redirect(url_for("addNewLanguage"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if language already exists
            db_cursor.execute(
                f"SELECT * FROM languageData WHERE languageName = ? AND languageId != ?",
                (languageName, languageId),
            )

            languageData = db_cursor.fetchone()

            if languageData is not None:
                flash("Language already exists", "danger")
                return redirect(url_for("addNewLanguage"))

            db_cursor.execute(
                f"UPDATE languageData SET languageName = ? WHERE languageId = ?",
                (languageName, languageId),
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewLanguage"))

            db_connection.commit()

            db_connection.close()

            return redirect(url_for("languageScreen"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


# /genre
@app.route("/genre", methods=["GET"])
def genreScreen():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if userRoleId != 2 and userRoleId != 0:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get all genres

        if userRoleId == 2:
            db_cursor.execute(f"SELECT * FROM genreData WHERE createdBy = ?", (userId,))
            genreList = db_cursor.fetchall()
        elif userRoleId == 0:
            db_cursor.execute(f"SELECT * FROM genreData")
            genreList = db_cursor.fetchall()

        db_connection.close()

        if genreList is None:
            flash(
                "No Genres found to add new songs! Add new Genres to continue", "danger"
            )
            return redirect(url_for("addNewGenre"))

        if userRoleId == 2:
            return render_template("creator/genre.html", genreList=genreList)
        elif userRoleId == 0:
            return render_template("admin/genre.html", genreList=genreList)

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/genre/new", methods=["GET", "POST"])
def addNewGenre():
    if request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            genreName = request.form.get("genreName")
            genreDescription = request.form.get("genreDescription")

            if len(str(genreName)) == 0 or len(str(genreDescription)) == 0:
                flash("Please fill all the fields", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if genre already exists
            db_cursor.execute(
                f"SELECT * FROM genreData WHERE genreName = ?", (genreName,)
            )
            genreData = db_cursor.fetchone()

            if genreData is not None:
                flash("Genre already exists", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_cursor.execute(
                f"INSERT INTO genreData (genreName, genreDescription, isActive, createdBy) VALUES (?, ?, ?, ?)",
                (genreName, genreDescription, "1", userId),
            )
            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_connection.commit()
            db_connection.close()

            if userRoleId == 2:
                return redirect(url_for("creatorDashboardScreen"))
            elif userRoleId == 0:
                return redirect(url_for("adminDashboard"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))
    elif request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            if userRoleId == 2:
                return render_template("creator/new_genre.html")
            elif userRoleId == 0:
                return render_template("admin/new_genre.html")

        except:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            if userRoleId == 2:
                return redirect(url_for("creatorDashboardScreen"))
            elif userRoleId == 0:
                return redirect(url_for("adminDashboard"))


@app.route("/genre/<genreId>/edit", methods=["GET", "POST"])
def editGenre(genreId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            if userRoleId != 0:
                # Get genre data
                db_cursor.execute(f"SELECT * FROM genreData WHERE genreId = ? AND createdBy = ?", (genreId,userId))
                genreData = db_cursor.fetchone()
            else:
                # Get genre data
                db_cursor.execute(f"SELECT * FROM genreData WHERE genreId = ?", (genreId,))
                genreData = db_cursor.fetchone()

            if genreData is None:
                flash("Genre not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            genreId = genreData[0]
            genreName = genreData[1]
            genreDescription = genreData[2]
            createdBy = genreData[4]

            # Check if user is creator of the genre
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            if userRoleId == 2:
                return render_template(
                    "creator/edit_genre.html",
                    genreId=genreId,
                    genreName=genreName,
                    genreDescription=genreDescription,
                )
            elif userRoleId == 0:
                return render_template(
                    "admin/edit_genre.html",
                    genreId=genreId,
                    genreName=genreName,
                    genreDescription=genreDescription,
                )

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    # POST
    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            genreName = request.form.get("genreName")
            genreDescription = request.form.get("genreDescription")

            if len(str(genreName)) == 0 or len(str(genreDescription)) == 0:
                flash("Please fill all the fields", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get genre data
            db_cursor.execute(f"SELECT * FROM genreData WHERE genreId = ?", (genreId,))
            genreData = db_cursor.fetchone()

            if genreData is None:
                flash("Genre not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            genreId = genreData[0]
            originalGenreName = genreData[1]
            genreDescription = genreData[2]
            createdBy = genreData[4]

            # Check if user is creator of the genre
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            # INSERT DATA AND IF SUCCESSFUL, UPLOAD FILES
            if len(str(genreName)) == 0 or len(str(genreDescription)) == 0:
                flash("Please fill all the fields", "danger")

            if originalGenreName != genreName:
                # Check if genre already exists
                db_cursor.execute(
                    f"SELECT * FROM genreData WHERE genreName = ?", (genreName,)
                )
                genreData = db_cursor.fetchone()

                if genreData is not None:
                    flash("Genre already exists", "danger")
                    if userRoleId == 2:
                        return redirect(url_for("creatorDashboardScreen"))
                    elif userRoleId == 0:
                        return redirect(url_for("adminDashboard"))

            db_cursor.execute(
                f"UPDATE genreData SET genreName = ?, genreDescription = ? WHERE genreId = ?",
                (genreName, genreDescription, genreId),
            )

            affectedRows = db_cursor.rowcount

            if affectedRows == 0:
                flash("Something went wrong", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_connection.commit()

            db_connection.close()

            return redirect(url_for("genreScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


# /album
@app.route("/album", methods=["GET"])
def albumScreen():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]
        searchQuery = request.args.get("search")

        if searchQuery is None:
            searchQuery = ""

        if userRoleId != 2 and userRoleId != 0:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get all albums

        if userRoleId == 2:
            db_cursor.execute(
                f"SELECT * FROM albumData WHERE createdBy = ? AND albumName LIKE ?",
                (userId, f"%{searchQuery}%"),
            )
            albumList = db_cursor.fetchall()
        elif userRoleId == 0:
            db_cursor.execute(
                f"SELECT * FROM albumData WHERE albumName LIKE ?", (f"%{searchQuery}%",)
            )
            albumList = db_cursor.fetchall()

        db_connection.close()

        if albumList is None:
            flash(
                "No Albums found to add new songs! Add new Albums to continue", "danger"
            )
            return redirect(url_for("addNewAlbum"))

        if userRoleId == 2:
            return render_template(
                "creator/album.html", albumList=albumList, searchQuery=searchQuery
            )
        elif userRoleId == 0:
            return render_template(
                "admin/album.html", albumList=albumList, searchQuery=searchQuery
            )

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/album/new", methods=["GET", "POST"])
def addNewAlbum():
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if user is creator
            db_cursor.execute(f"SELECT * FROM userData WHERE userId = ?", (userId,))
            userData = db_cursor.fetchone()

            if userData is None:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            db_connection.close()

            if userRoleId == 2:
                return render_template("creator/new_album.html")
            elif userRoleId == 0:
                return render_template("admin/new_album.html")

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            albumName = request.form.get("albumName")
            albumDescription = request.form.get("albumDescription")
            releaseDate = request.form.get("releaseDate")
            albumCover = request.files["albumCover"]

            if (
                len(str(albumName)) == 0
                or len(str(albumDescription)) == 0
                or len(str(releaseDate)) == 0
                or len(str(albumCover.filename)) == 0
            ):
                flash("Please fill all the fields", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Check if album already exists
            db_cursor.execute(
                f"SELECT * FROM albumData WHERE albumName = ?", (albumName,)
            )
            albumData = db_cursor.fetchone()

            if albumData is not None:
                flash("Album already exists", "danger")
                return redirect(url_for("addNewAlbum"))

            db_cursor.execute(
                f"INSERT INTO albumData (albumName, albumDescription, releaseDate, isActive, createdBy, albumCoverExt) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    albumName,
                    albumDescription,
                    releaseDate,
                    "1",
                    userId,
                    albumCover.filename.split(".")[-1],
                ),
            )
            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewAlbum"))

            albumId = db_cursor.lastrowid

            db_connection.commit()
            db_connection.close()

            # Upload album cover
            albumCover.save(
                f"static/music/album/{albumId}.{albumCover.filename.split('.')[-1]}"
            )

            return redirect(url_for("albumScreen"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/album/<albumId>/edit", methods=["GET", "POST"])
def editAlbum(albumId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get album data
            db_cursor.execute(f"SELECT * FROM albumData WHERE albumId = ?", (albumId,))
            albumData = db_cursor.fetchone()

            if albumData is None:
                flash("Album not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            albumId = albumData[0]
            albumName = albumData[1]
            albumDescription = albumData[2]
            releaseDate = albumData[4]
            createdBy = albumData[7]
            albumCoverExt = albumData[11]

            # Check if user is creator of the album
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            if userRoleId == 2:
                return render_template(
                    "creator/edit_album.html",
                    albumId=albumId,
                    albumName=albumName,
                    albumDescription=albumDescription,
                    releaseDate=releaseDate,
                    albumCoverExt=albumCoverExt,
                )

            elif userRoleId == 0:
                return render_template(
                    "admin/edit_album.html",
                    albumId=albumId,
                    albumName=albumName,
                    albumDescription=albumDescription,
                    releaseDate=releaseDate,
                    albumCoverExt=albumCoverExt,
                )

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    # POST
    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            albumName = request.form.get("albumName")
            albumDescription = request.form.get("albumDescription")
            releaseDate = request.form.get("releaseDate")
            albumCover = request.files["albumCover"]

            if (
                len(str(albumName)) == 0
                or len(str(albumDescription)) == 0
                or len(str(releaseDate)) == 0
            ):
                flash("Please fill all the fields", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get album data
            db_cursor.execute(f"SELECT * FROM albumData WHERE albumId = ?", (albumId,))
            albumData = db_cursor.fetchone()

            if albumData is None:
                flash("Album not found", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            albumId = albumData[0]
            originalAlbumName = albumData[1]
            albumDescription = albumData[2]
            releaseDate = albumData[4]
            createdBy = albumData[7]
            albumCoverExt = albumData[11]

            # Check if user is creator of the album
            if createdBy != userId and userRoleId != 0 and userRoleId == 2:
                flash("Unauthorized Access", "danger")
                if userRoleId == 2:
                    return redirect(url_for("creatorDashboardScreen"))
                elif userRoleId == 0:
                    return redirect(url_for("adminDashboard"))

            # INSERT DATA AND IF
            if (
                len(str(albumName)) == 0
                or len(str(albumDescription)) == 0
                or len(str(releaseDate)) == 0
            ):
                flash("Please fill all the fields", "danger")
                return redirect(url_for("addNewAlbum"))

            if originalAlbumName != albumName:
                # Check if album already exists
                db_cursor.execute(
                    f"SELECT * FROM albumData WHERE albumName = ?", (albumName,)
                )
                albumData = db_cursor.fetchone()

                if albumData is not None:
                    flash("Album already exists", "danger")
                    return redirect(url_for("addNewAlbum"))

            db_cursor.execute(
                f"UPDATE albumData SET albumName = ?, albumDescription = ?, releaseDate = ? WHERE albumId = ?",
                (albumName, albumDescription, releaseDate, albumId),
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("addNewAlbum"))

            # Upload album cover
            if albumCover.filename != "":
                db_cursor.execute(
                    f"UPDATE albumData SET albumCoverExt = ? WHERE albumId = ?",
                    (albumCover.filename.split(".")[-1], albumId),
                )
                # Remove old file
                os.remove(f"static/music/album/{albumId}.{albumCoverExt}")
                # Upload new file
                albumCover.save(
                    f"static/music/album/{albumId}.{albumCover.filename.split('.')[-1]}"
                )

            db_connection.commit()
            db_connection.close()
            return redirect(url_for("albumScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()
            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/album/<albumId>", methods=["GET"])
def albumDetails(albumId):
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get album data
        db_cursor.execute(f"SELECT * FROM albumData WHERE albumId = ?", (albumId,))
        albumData = db_cursor.fetchone()

        if albumData is None:
            flash("Album not found", "danger")
            return redirect(url_for("albumScreen"))

        albumId = albumData[0]
        albumName = albumData[1]
        albumDescription = albumData[2]
        releaseDate = albumData[4]
        createdBy = albumData[7]
        albumCoverExt = albumData[11]

        # Get all songs in the album
        db_cursor.execute(
            f"SELECT songData.songId, songData.songName, genreData.genreName, songData.songLyrics, songData.audioFileExt, songData.imageFileExt, songData.isActive, languageData.languageName FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId WHERE songId IN (SELECT songId FROM albumSongs WHERE albumId = ?)",
            (albumId,),
        )

        songList = db_cursor.fetchall()

        db_connection.close()

        if songList is None:
            songList = []

        if userRoleId == 2:
            return render_template(
            "creator/album_details.html",
            albumId=albumId,
            albumName=albumName,
            albumDescription=albumDescription,
            releaseDate=releaseDate,
            createdBy=createdBy,
            albumCoverExt=albumCoverExt,
            songList=songList,
        )

        elif userRoleId == 0:
            return render_template(
            "admin/album_details.html",
            albumId=albumId,
            albumName=albumName,
            albumDescription=albumDescription,
            releaseDate=releaseDate,
            createdBy=createdBy,
            albumCoverExt=albumCoverExt,
            songList=songList,
        )

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/album/<albumId>/addSong", methods=["GET"])
def addSongToAlbum(albumId):
    # Show all songs that are not in any album
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get album data
        db_cursor.execute(f"SELECT * FROM albumData WHERE albumId = ?", (albumId,))
        albumData = db_cursor.fetchone()

        if albumData is None:
            flash("Album not found", "danger")
            return redirect(url_for("albumScreen"))

        albumName = albumData[1]
        albumDescription = albumData[2]
        releaseDate = albumData[4]
        createdBy = albumData[7]
        albumCoverExt = albumData[11]

        # Get all songs that are not in any album of the creator
        db_cursor.execute(
            f"SELECT songData.songId, songData.songName, genreData.genreName, songData.songLyrics, songData.audioFileExt, songData.imageFileExt, songData.isActive, languageData.languageName FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId WHERE songId NOT IN (SELECT songId FROM albumSongs WHERE albumId IN (SELECT albumId FROM albumData WHERE createdBy = ?))",
            (userId,),
        )
        songList = db_cursor.fetchall()

        db_connection.close()

        if songList is None:
            songList = []

        return render_template(
            "creator/add_song_to_album.html",
            songList=songList,
            albumId=albumId,
            albumName=albumName,
            albumDescription=albumDescription,
            releaseDate=releaseDate,
            createdBy=createdBy,
            albumCoverExt=albumCoverExt,
        )

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()

        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/album/<albumId>/song/<songId>/unlink", methods=["POST"])
def unlinkSongFromAlbum(albumId, songId):
    if request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get album data
            db_cursor.execute(f"SELECT * FROM albumData WHERE albumId = ?", (albumId,))
            albumData = db_cursor.fetchone()

            if albumData is None:
                flash("Album not found", "danger")
                return redirect(url_for("albumScreen"))

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                return redirect(url_for("albumScreen"))

            # Check if song is already linked to album
            db_cursor.execute(
                f"SELECT * FROM albumSongs WHERE albumId = ? AND songId = ?",
                (albumId, songId),
            )

            albumSongData = db_cursor.fetchone()

            if albumSongData is None:
                flash("Song not linked to album", "danger")
                return redirect(url_for("albumScreen"))

            db_cursor.execute(
                f"DELETE FROM albumSongs WHERE albumId = ? AND songId = ?",
                (albumId, songId),
            )

            affectedRows = db_cursor.rowcount

            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("albumScreen"))

            db_connection.commit()

            db_connection.close()

            return redirect(url_for("albumScreen"))

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/album/<albumId>/song/<songId>/link", methods=["POST"])
def linkSongToAlbum(albumId, songId):
    if request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 2 and userRoleId != 0:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get album data
            db_cursor.execute(f"SELECT * FROM albumData WHERE albumId = ?", (albumId,))
            albumData = db_cursor.fetchone()

            if albumData is None:
                flash("Album not found", "danger")
                return redirect(url_for("albumScreen"))

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                return redirect(url_for("albumScreen"))

            # Check if song is already linked to album
            db_cursor.execute(
                f"SELECT * FROM albumSongs WHERE albumId = ? AND songId = ?",
                (albumId, songId),
            )

            albumSongData = db_cursor.fetchone()

            if albumSongData is not None:
                flash("Song already linked to album", "danger")
                return redirect(url_for("albumScreen"))

            db_cursor.execute(
                f"INSERT INTO albumSongs (albumId, songId) VALUES (?, ?)",
                (albumId, songId),
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("albumScreen"))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("albumScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


# /playlist
@app.route("/playlist", methods=["GET"])
def playlistScreen():
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]
        searchQuery = request.args.get("search")

        if searchQuery is None:
            searchQuery = ""

        if userRoleId != 1 and userRoleId != 0:
            flash("Unauthorized Access", "danger")
            return redirect(url_for("loginScreen"))

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        if userRoleId == 1:
            # Get all playlists
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistName LIKE ? AND userId = ?",
                (f"%{searchQuery}%", userId),
            )
            playlistList = db_cursor.fetchall()

            # Get public playlists
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistName LIKE ? AND isPublic = '1' AND userId != ?",
                (f"%{searchQuery}%", userId),
            )
            publicPlaylistList = db_cursor.fetchall()
        
        elif userRoleId == 0:
            # Get all playlists
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistName LIKE ?",
                (f"%{searchQuery}%",),
            )
            playlistList = db_cursor.fetchall()

        db_connection.close()

        if playlistList is None:
            playlistList = []

        if userRoleId == 1:
            return render_template(
                "user/playlist.html",
                playlistList=playlistList,
                publicPlaylistList=publicPlaylistList,
                searchQuery=searchQuery,
            )
        elif userRoleId == 0:
            return render_template(
                "admin/playlist.html", playlistList=playlistList, searchQuery=searchQuery
            )

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/playlist/<playlistId>", methods=["GET"])
def playlistDetails(playlistId):
    try:
        secretToken = session["secretToken"]
        userId = session["userId"]
        userName = session["userName"]
        userEmail = session["userEmail"]
        userRoleId = session["userRoleId"]

        if (
            len(str(secretToken)) == 0
            or len(str(userId)) == 0
            or len(str(userName)) == 0
            or len(str(userEmail)) == 0
            or len(str(userRoleId)) == 0
        ):
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        if decryptedToken == -2:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))
        elif decryptedToken == -1:
            flash("Session Expired", "danger")
            return redirect(url_for("loginScreen"))

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Get playlist data
        db_cursor.execute(
            f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
        )
        playlistData = db_cursor.fetchone()

        if playlistData is None:
            flash("Playlist not found", "danger")
            return redirect(url_for("playlistScreen"))

        playlistId = playlistData[0]
        playlistName = playlistData[1]
        playlistDescription = playlistData[2]
        playListUserId = playlistData[3]
        isPublic = playlistData[4]

        # Get all songs in the playlist
        db_cursor.execute(
            f"SELECT songData.songId, songData.songName, genreData.genreName, songData.songLyrics, songData.audioFileExt, songData.imageFileExt, songData.isActive, languageData.languageName FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId WHERE songId IN (SELECT songId FROM playlistSongs WHERE playlistId = ?)",
            (playlistId,),
        )

        songList = db_cursor.fetchall()

        db_connection.close()

        if songList is None:
            songList = []

        notUserPlaylist = (playListUserId != userId)

        if userRoleId == 1:
            return render_template(
                "user/playlist_details.html",
                playlistId=playlistId,
                playlistName=playlistName,
                playlistDescription=playlistDescription,
                isPublic=isPublic,
                songList=songList,
                notUserPlaylist=notUserPlaylist,
            )
        elif userRoleId == 0:
            return render_template(
                "admin/playlist_details.html",
                playlistId=playlistId,
                playlistName=playlistName,
                playlistDescription=playlistDescription,
                isPublic=isPublic,
                songList=songList,
                notUserPlaylist=notUserPlaylist,
            )

    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        flash("Something Went Wrong.\nPlease try again later.", "danger")
        return redirect(url_for("loginScreen"))


@app.route("/playlist/<playlistId>/addSong", methods=["GET"])
def addSongToPlaylist(playlistId):
    # Show all songs that are not in any playlist
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get playlist data
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
            )
            playlistData = db_cursor.fetchone()

            if playlistData is None:
                flash("Playlist not found", "danger")
                return redirect(url_for("playlistScreen"))

            playlistName = playlistData[1]
            playlistDescription = playlistData[2]
            userId = playlistData[3]
            isPublic = playlistData[4]

            # Get all songs that are not in any playlist of the creator
            db_cursor.execute(
                f"SELECT songData.songId, songData.songName, genreData.genreName, songData.songLyrics, songData.audioFileExt, songData.imageFileExt, songData.isActive, languageData.languageName FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId WHERE songId NOT IN (SELECT songId FROM playlistSongs WHERE playlistId = ?)",
                (playlistId,),
            )
            songList = db_cursor.fetchall()

            db_connection.close()

            if songList is None:
                songList = []

            return render_template(
                "user/add_song_to_playlist.html",
                songList=songList,
                playlistId=playlistId,
                playlistName=playlistName,
                playlistDescription=playlistDescription,
                isPublic=isPublic,
            )

        except Exception as e:
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/playlist/<playlistId>/song/<songId>/unlink", methods=["POST"])
def unlinkSongFromPlaylist(playlistId, songId):
    if request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get playlist data
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
            )
            playlistData = db_cursor.fetchone()

            if playlistData is None:
                flash("Playlist not found", "danger")
                return redirect(url_for("playlistScreen"))

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                return redirect(url_for("playlistScreen"))

            # Check if song is already linked to playlist
            db_cursor.execute(
                f"SELECT * FROM playlistSongs WHERE playlistId = ? AND songId = ?",
                (playlistId, songId),
            )

            playlistSongData = db_cursor.fetchone()

            if playlistSongData is None:
                flash("Song not linked to playlist", "danger")
                return redirect(url_for("playlistScreen"))

            db_cursor.execute(
                f"DELETE FROM playlistSongs WHERE playlistId = ? AND songId = ?",
                (playlistId, songId),
            )

            affectedRows = db_cursor.rowcount

            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("playlistScreen"))

            db_connection.commit()

            db_connection.close()

            return redirect(url_for("playlistScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/playlist/<playlistId>/song/<songId>/link", methods=["POST"])
def linkSongToPlaylist(playlistId, songId):
    if request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get playlist data
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
            )
            playlistData = db_cursor.fetchone()

            if playlistData is None:
                flash("Playlist not found", "danger")
                return redirect(url_for("playlistScreen"))

            # Get song data
            db_cursor.execute(f"SELECT * FROM songData WHERE songId = ?", (songId,))
            songData = db_cursor.fetchone()

            if songData is None:
                flash("Song not found", "danger")
                return redirect(url_for("playlistScreen"))

            # Check if song is already linked to playlist
            db_cursor.execute(
                f"SELECT * FROM playlistSongs WHERE playlistId = ? AND songId = ?",
                (playlistId, songId),
            )

            playlistSongData = db_cursor.fetchone()

            if playlistSongData is not None:
                flash("Song already linked to playlist", "danger")
                return redirect(url_for("playlistScreen"))

            db_cursor.execute(
                f"INSERT INTO playlistSongs (playlistId, songId) VALUES (?, ?)",
                (playlistId, songId),
            )

            affectedRows = db_cursor.rowcount
            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("playlistScreen"))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("playlistScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))


@app.route("/playlist/new", methods=["GET", "POST"])
def newPlaylist():
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            return render_template("user/new_playlist.html")

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            playlistName = request.form.get("playlistName")
            playlistDescription = request.form.get("playlistDescription")
            isPublic = request.form.get("isPublic")

            if (
                len(str(playlistName)) == 0
                or len(str(playlistDescription)) == 0
                or len(str(isPublic)) == 0
            ):
                flash("Please fill all the fields", "danger")
                return redirect(url_for("newPlaylist"))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            db_cursor.execute(
                f"INSERT INTO playlistData (playlistName, playlistDescription, userId, isPublic) VALUES (?, ?, ?, ?)",
                (playlistName, playlistDescription, userId, isPublic),
            )
            affectedRows = db_cursor.rowcount

            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("newPlaylist"))

            playlistId = db_cursor.lastrowid

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("userDashboardScreen"))

        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))

@app.route("/playlist/<playlistId>/edit", methods=["GET", "POST"])
def editPlaylist(playlistId):
    if request.method == "GET":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))

            decryptedToken = validateToken(
                secretToken.split(",")[0],
                secretToken.split(",")[1],
                secretToken.split(",")[2],
            )

            if decryptedToken == -2:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            elif decryptedToken == -1:
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            
            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            # Get playlist data
            db_cursor.execute(
                f"SELECT * FROM playlistData WHERE playlistId = ? AND userId = ?", (playlistId,userId)
            )
            playlistData = db_cursor.fetchone()

            if playlistData is None:
                flash("Playlist not found", "danger")
                return redirect(url_for("playlistScreen"))
            
            playlistName = playlistData[1]
            playlistDescription = playlistData[2]
            isPublic = playlistData[4]


            db_connection.close()
            
            return render_template("user/edit_playlist.html", playlistId=playlistId, playlistName=playlistName, playlistDescription=playlistDescription, isPublic=isPublic)
        
        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))
        
    elif request.method == "POST":
        try:
            secretToken = session["secretToken"]
            userId = session["userId"]
            userName = session["userName"]
            userEmail = session["userEmail"]
            userRoleId = session["userRoleId"]

            if userRoleId != 1:
                flash("Unauthorized Access", "danger")
                return redirect(url_for("loginScreen"))

            if (
                len(str(secretToken)) == 0
                or len(str(userId)) == 0
                or len(str(userName)) == 0
                or len(str(userEmail)) == 0
                or len(str(userRoleId)) == 0
            ):
                flash("Session Expired", "danger")
                return redirect(url_for("loginScreen"))
            
            playlistName = request.form.get("playlistName")
            playlistDescription = request.form.get("playlistDescription")
            isPublic = request.form.get("isPublic")

            if (
                len(str(playlistName)) == 0
                or len(str(playlistDescription)) == 0
                or len(str(isPublic)) == 0
            ):
                flash("Please fill all the fields", "danger")
                return redirect(url_for("editPlaylist", playlistId=playlistId))

            db_connection = sqlite3.connect("./schema/app_data.db")
            db_cursor = db_connection.cursor()

            db_cursor.execute('SELECT * FROM playlistData WHERE playlistId = ? AND userId = ?', (playlistId, userId))
            playlistData = db_cursor.fetchone()

            if playlistData is None:
                flash("Playlist not found", "danger")
                return redirect(url_for("playlistScreen"))
            
            oldName = playlistData[1]

            if oldName != playlistName:
                db_cursor.execute('SELECT * FROM playlistData WHERE playlistName = ? AND userId = ?', (playlistName, userId))
                playlistData = db_cursor.fetchone()

                if playlistData is not None:
                    flash("Playlist name already exists", "danger")
                    return redirect(url_for("editPlaylist", playlistId=playlistId))

            db_cursor.execute(
                f"UPDATE playlistData SET playlistName = ?, playlistDescription = ?, isPublic = ? WHERE playlistId = ?",
                (playlistName, playlistDescription, isPublic, playlistId),
            )
            affectedRows = db_cursor.rowcount

            if affectedRows == 0:
                flash("Something went wrong", "danger")
                return redirect(url_for("editPlaylist", playlistId=playlistId))

            db_connection.commit()
            db_connection.close()

            return redirect(url_for("playlistScreen"))
        
        except Exception as e:
            print(e)
            f = open("logs/errorLogs.txt", "a")
            f.write(f"[ERROR] {datetime.now()}: {e}\n")
            f.close()

            flash("Something Went Wrong.\nPlease try again later.", "danger")
            return redirect(url_for("loginScreen"))
        

# API for songs, playlists CRUD
        
@app.route("/api/login", methods=["POST"])
def apiLogin():
    try:
        # JSON Data
        jsonData = request.json

        userEmail = jsonData["userEmail"]
        userPassword = jsonData["userPassword"]

        if userEmail is None or userPassword is None:
            return jsonify({"status": "error", "message": "Please fill all the fields"})

        if (
            len(str(userEmail)) == 0
            or len(str(userPassword)) == 0
        ):
            return jsonify({"status": "error", "message": "Please fill all the fields"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        db_cursor.execute(
            f"SELECT * FROM userData WHERE userEmail = ? AND userPassword = ?",
            (userEmail, userPassword),
        )
        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})

        userId = userData[0]
        userName = userData[1]
        userEmail = userData[2]
        userRoleId = userData[4]

        # Generate Token
        secretToken = generateToken({
            "userId": userId,
            "userName": userName,
            "userEmail": userEmail,
            "userRoleId": userRoleId,
        })

        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Login Successful",
                "secretToken": secretToken,
                "userId": userId,
                "userName": userName,
                "userEmail": userEmail,
                "userRoleId": userRoleId,
            }
        )

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})

@app.route("/api/song", methods=["GET"])
def apiGetAllSongs():
    try:
        header = request.headers.get("Authorization")
        if header is None:
            return jsonify({"status": "error", "message": "Session Expired"})
        
        secretToken = header.split(" ")[1]

        if len(str(secretToken)) == 0 or secretToken is None:
            return jsonify({"status": "error", "message": "Session Expired"})

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        userId = decryptedToken["userId"]

        if decryptedToken == -2:
            return jsonify({"status": "error", "message": "Session Expired"})
        elif decryptedToken == -1:
            return jsonify({"status": "error", "message": "Session Expired"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user Exists and check role
        db_cursor.execute(
            f"SELECT userRoleId FROM userData WHERE userId = ?", (userId,)
        )

        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})
        
        userRoleId = userData[0]

        if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
            return jsonify({"status": "error", "message": "Unauthorized Access"})
        
        # Get all songs
        db_cursor.execute(
            f"SELECT * FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId"
        )

        songList = db_cursor.fetchall()

        # dict of songs
        songList = [dict(zip([key[0] for key in db_cursor.description], song)) for song in songList]
        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Songs Fetched",
                "songList": songList,
            }
        )

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})
    
@app.route("/api/song/<songId>", methods=["GET"])
def apiGetSong(songId):
    try:
        header = request.headers.get("Authorization")
        if header is None:
            return jsonify({"status": "error", "message": "Session Expired"})
        
        secretToken = header.split(" ")[1]

        if len(str(secretToken)) == 0 or secretToken is None:
            return jsonify({"status": "error", "message": "Session Expired"})

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        userId = decryptedToken["userId"]

        if decryptedToken == -2:
            return jsonify({"status": "error", "message": "Session Expired"})
        elif decryptedToken == -1:
            return jsonify({"status": "error", "message": "Session Expired"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user Exists and check role
        db_cursor.execute(
            f"SELECT userRoleId FROM userData WHERE userId = ?", (userId,)
        )

        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})
        
        userRoleId = userData[0]

        if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
            return jsonify({"status": "error", "message": "Unauthorized Access"})
        
        # Get song
        db_cursor.execute(
            f"SELECT * FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId WHERE songId = ?", (songId,)
        )

        songData = db_cursor.fetchone()
        if songData is None:
            return jsonify({"status": "error", "message": "Song not found"})
        
        songData = dict(zip([key[0] for key in db_cursor.description], songData))

        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Song Fetched",
                "songData": songData,
            }
        )

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})
    
# playlist
@app.route("/api/playlist", methods=["GET"])
def apiGetAllPlaylists():
    try:
        header = request.headers.get("Authorization")
        if header is None:
            return jsonify({"status": "error", "message": "Session Expired"})
        
        secretToken = header.split(" ")[1]

        if len(str(secretToken)) == 0 or secretToken is None:
            return jsonify({"status": "error", "message": "Session Expired"})

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        userId = decryptedToken["userId"]

        if decryptedToken == -2:
            return jsonify({"status": "error", "message": "Session Expired"})
        elif decryptedToken == -1:
            return jsonify({"status": "error", "message": "Session Expired"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user Exists and check role
        db_cursor.execute(
            f"SELECT userRoleId FROM userData WHERE userId = ?", (userId,)
        )

        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})
        
        userRoleId = userData[0]

        if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
            return jsonify({"status": "error", "message": "Unauthorized Access"})
        
        # Get all playlists
        db_cursor.execute(
            f"SELECT * FROM playlistData"
        )

        playlistList = db_cursor.fetchall()
        if playlistList is None:
            return jsonify({"status": "error", "message": "No playlists found"})
        
        playlistList = [dict(zip([key[0] for key in db_cursor.description], playlist)) for playlist in playlistList]

        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Playlists Fetched",
                "playlistList": playlistList,
            }
        )

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})
    
@app.route("/api/playlist/<playlistId>", methods=["GET"])
def apiGetPlaylist(playlistId):
    try:
        header = request.headers.get("Authorization")
        if header is None:
            return jsonify({"status": "error", "message": "Session Expired"})
        
        secretToken = header.split(" ")[1]

        if len(str(secretToken)) == 0 or secretToken is None:
            return jsonify({"status": "error", "message": "Session Expired"})

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        userId = decryptedToken["userId"]

        if decryptedToken == -2:
            return jsonify({"status": "error", "message": "Session Expired"})
        elif decryptedToken == -1:
            return jsonify({"status": "error", "message": "Session Expired"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user Exists and check role
        db_cursor.execute(
            f"SELECT userRoleId FROM userData WHERE userId = ?", (userId,)
        )

        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})
        
        userRoleId = userData[0]

        if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
            return jsonify({"status": "error", "message": "Unauthorized Access"})
        
        # Get playlist
        db_cursor.execute(
            f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
        )

        playlistData = db_cursor.fetchone()
        if playlistData is None:
            return jsonify({"status": "error", "message": "Playlist not found"})
        
        playlistData = dict(zip([key[0] for key in db_cursor.description], playlistData))

        # Get all songs in the playlist
        db_cursor.execute(
            f"SELECT * FROM songData JOIN genreData ON songData.songGenreId = genreData.genreId JOIN languageData ON songData.songLanguageId = languageData.languageId WHERE songId IN (SELECT songId FROM playlistSongs WHERE playlistId = ?)",
            (playlistId,),
        )

        songList = db_cursor.fetchall()
        if songList is None:
            songList = []
        else:
            songList = [dict(zip([key[0] for key in db_cursor.description], song)) for song in songList]

        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Playlist Fetched",
                "playlistData": playlistData,
                "songList": songList,
            }
        )

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})
    
@app.route("/api/playlist/<playlistId>/song/<songId>/link", methods=["POST"])
def apiLinkSongToPlaylist(playlistId, songId):
    try:
        header = request.headers.get("Authorization")
        if header is None:
            return jsonify({"status": "error", "message": "Session Expired"})
        
        secretToken = header.split(" ")[1]

        if len(str(secretToken)) == 0 or secretToken is None:
            return jsonify({"status": "error", "message": "Session Expired"})

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        userId = decryptedToken["userId"]

        if decryptedToken == -2:
            return jsonify({"status": "error", "message": "Session Expired"})
        elif decryptedToken == -1:
            return jsonify({"status": "error", "message": "Session Expired"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user Exists and check role
        db_cursor.execute(
            f"SELECT userRoleId FROM userData WHERE userId = ?", (userId,)
        )

        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})
        
        userRoleId = userData[0]

        if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
            return jsonify({"status": "error", "message": "Unauthorized Access"})
        
        # Get playlist
        db_cursor.execute(
            f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
        )

        playlistData = db_cursor.fetchone()
        if playlistData is None:
            return jsonify({"status": "error", "message": "Playlist not found"})
        
        # Get song
        db_cursor.execute(
            f"SELECT * FROM songData WHERE songId = ?", (songId,)
        )

        songData = db_cursor.fetchone()
        if songData is None:
            return jsonify({"status": "error", "message": "Song not found"})
        
        # Check if song is already linked to playlist
        db_cursor.execute(
            f"SELECT * FROM playlistSongs WHERE playlistId = ? AND songId = ?",
            (playlistId, songId),
        )

        playlistSongData = db_cursor.fetchone()

        if playlistSongData is not None:
            return jsonify({"status": "error", "message": "Song already linked to playlist"})
        
        db_cursor.execute(
            f"INSERT INTO playlistSongs (playlistId, songId) VALUES (?, ?)",
            (playlistId, songId),
        )

        affectedRows = db_cursor.rowcount
        if affectedRows == 0:
            return jsonify({"status": "error", "message": "Something went wrong"})
        
        db_connection.commit()
        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Song linked to playlist",
            }
        )
    
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})
    
@app.route("/api/playlist/<playlistId>/song/<songId>/unlink", methods=["POST"])
def apiUnlinkSongFromPlaylist(playlistId, songId):
    try:
        header = request.headers.get("Authorization")
        if header is None:
            return jsonify({"status": "error", "message": "Session Expired"})
        
        secretToken = header.split(" ")[1]

        if len(str(secretToken)) == 0 or secretToken is None:
            return jsonify({"status": "error", "message": "Session Expired"})

        decryptedToken = validateToken(
            secretToken.split(",")[0],
            secretToken.split(",")[1],
            secretToken.split(",")[2],
        )

        userId = decryptedToken["userId"]

        if decryptedToken == -2:
            return jsonify({"status": "error", "message": "Session Expired"})
        elif decryptedToken == -1:
            return jsonify({"status": "error", "message": "Session Expired"})

        db_connection = sqlite3.connect("./schema/app_data.db")
        db_cursor = db_connection.cursor()

        # Check if user Exists and check role
        db_cursor.execute(
            f"SELECT userRoleId FROM userData WHERE userId = ?", (userId,)
        )

        userData = db_cursor.fetchone()

        if userData is None:
            return jsonify({"status": "error", "message": "Invalid Credentials"})
        
        userRoleId = userData[0]

        if userRoleId != 1 and userRoleId != 0 and userRoleId != 2:
            return jsonify({"status": "error", "message": "Unauthorized Access"})
        
        # Get playlist
        db_cursor.execute(
            f"SELECT * FROM playlistData WHERE playlistId = ?", (playlistId,)
        )

        playlistData = db_cursor.fetchone()
        if playlistData is None:
            return jsonify({"status": "error", "message": "Playlist not found"})
        
        # Get song
        db_cursor.execute(
            f"SELECT * FROM songData WHERE songId = ?", (songId,)
        )

        songData = db_cursor.fetchone()
        if songData is None:
            return jsonify({"status": "error", "message": "Song not found"})
        
        # Check if song is already linked to playlist
        db_cursor.execute(
            f"SELECT * FROM playlistSongs WHERE playlistId = ? AND songId = ?",
            (playlistId, songId),
        )

        playlistSongData = db_cursor.fetchone()

        if playlistSongData is None:
            return jsonify({"status": "error", "message": "Song not linked to playlist"})
        
        db_cursor.execute(
            f"DELETE FROM playlistSongs WHERE playlistId = ? AND songId = ?",
            (playlistId, songId),
        )

        affectedRows = db_cursor.rowcount
        if affectedRows == 0:
            return jsonify({"status": "error", "message": "Something went wrong"})
        
        db_connection.commit()
        db_connection.close()

        return jsonify(
            {
                "status": "success",
                "message": "Song unlinked from playlist",
            }
        )
    
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Something Went Wrong"})

if __name__ == "__main__":
    #reinitializeDatabase()
    #initEnvironment()
    #generateKey()

    app.run(debug=True, port=5000)
