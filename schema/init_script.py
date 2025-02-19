# export string for init script

import sqlite3
from datetime import datetime
import os

init_query = """
/* SQLITE 3 Music Streaming App */


DROP TABLE IF EXISTS "playlistSongs";
DROP TABLE IF EXISTS "playlistData";
DROP TABLE IF EXISTS "songComments";
DROP TABLE IF EXISTS "songPlays";
DROP TABLE IF EXISTS "songLikes";
DROP TABLE IF EXISTS "songArtists";
DROP TABLE IF EXISTS "songData";
DROP TABLE IF EXISTS "albumLikes";
DROP TABLE IF EXISTS "albumData";
DROP TABLE IF EXISTS "genreData";
DROP TABLE IF EXISTS "languageData";
DROP TABLE IF EXISTS "userFollows";
DROP TABLE IF EXISTS "userData";
DROP TABLE IF EXISTS "userRole";

CREATE TABLE IF NOT EXISTS "userRole" (
    "roleId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "roleName" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "userData" (
    "userId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "userName" TEXT NOT NULL,
    "userEmail" TEXT NOT NULL UNIQUE,
    "userPassword" TEXT NOT NULL,
    "userRoleId" INTEGER NOT NULL,
    "userDob" TEXT NOT NULL,
    "userGender" TEXT NOT NULL,
    "accountStatus" TEXT NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastUpdatedAt" TEXT NULL,
    FOREIGN KEY ("userRoleId") REFERENCES "userRole" ("roleId"),
    CHECK ("accountStatus" IN ("0", "1", "2", "3")),
    CHECK ("userGender" IN ("M", "F", "O"))
);

CREATE TABLE IF NOT EXISTS "userFollows" (
    "userId" INTEGER NOT NULL,
    "followerId" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("userId", "followerId"),
    FOREIGN KEY ("userId") REFERENCES "userData" ("userId"),
    FOREIGN KEY ("followerId") REFERENCES "userData" ("userId")
);

CREATE TABLE IF NOT EXISTS "languageData" (
    "languageId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "languageName" TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "genreData" (
    "genreId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "genreName" TEXT NOT NULL UNIQUE,
    "genreDescription" TEXT NULL,
    "isActive" TEXT NOT NULL,
    "createdBy" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastUpdatedBy" INTEGER NULL,
    "lastUpdatedAt" TEXT NULL,
    FOREIGN KEY ("createdBy") REFERENCES "userData" ("userId"),
    FOREIGN KEY ("lastUpdatedBy") REFERENCES "userData" ("userId"),
    CHECK ("isActive" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "albumData" (
    "albumId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "albumName" TEXT NOT NULL,
    "albumDescription" TEXT NULL,
    "albumRating" TEXT NOT NULL DEFAULT "0",
    "releaseDate" TEXT NOT NULL,
    "albumLikesCount" INTEGER NOT NULL DEFAULT 0,
    "isActive" TEXT NOT NULL,
    "createdBy" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastUpdatedBy" INTEGER NULL,
    "lastUpdatedAt" TEXT NULL,
    "albumCoverExt" TEXT NOT NULL,
    FOREIGN KEY ("createdBy") REFERENCES "userData" ("userId"),
    FOREIGN KEY ("lastUpdatedBy") REFERENCES "userData" ("userId"),
    CHECK ("albumRating" IN ("0", "1", "2", "3", "4", "5")),
    CHECK ("isActive" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "albumLikes" (
    "albumId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "isLike" TEXT NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("albumId", "userId"),
    FOREIGN KEY ("albumId") REFERENCES "albumData" ("albumId"),
    FOREIGN KEY ("userId") REFERENCES "userData" ("userId"),
    CHECK ("isLike" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "songData" (
    "songId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "songName" TEXT NOT NULL,
    "songDescription" TEXT NULL,
    "songRating" TEXT NOT NULL DEFAULT "0",
    "songLyrics" TEXT NULL,
    "songDuration" TEXT NULL,
    "songReleaseDate" TEXT NOT NULL,
    "songGenreId" INTEGER NOT NULL,
    "songAlbumId" INTEGER NULL,
    "songLanguageId" INTEGER NOT NULL,
    "likesCount" INTEGER NOT NULL DEFAULT 0,
    "isActive" TEXT NOT NULL,
    "createdBy" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastUpdatedBy" INTEGER NULL,
    "lastUpdatedAt" TEXT NULL,
    "audioFileExt" TEXT NOT NULL,
    "imageFileExt" INTEGER NOT NULL,
    FOREIGN KEY ("songGenreId") REFERENCES "genreData" ("genreId"),
    FOREIGN KEY ("songAlbumId") REFERENCES "albumData" ("albumId"),
    FOREIGN KEY ("createdBy") REFERENCES "userData" ("userId"),
    FOREIGN KEY ("lastUpdatedBy") REFERENCES "userData" ("userId"),
    FOREIGN KEY ("songLanguageId") REFERENCES "languageData" ("languageId"),
    CHECK ("songRating" IN ("0", "1", "2", "3", "4", "5")),
    CHECK ("isActive" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "songArtists" (
    "songId" INTEGER NOT NULL,
    "artistId" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("songId", "artistId"),
    FOREIGN KEY ("songId") REFERENCES "songData" ("songId"),
    FOREIGN KEY ("artistId") REFERENCES "userData" ("userId")
);

CREATE TABLE IF NOT EXISTS "songLikes" (
    "songId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "isLike" TEXT NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("songId", "userId"),
    FOREIGN KEY ("songId") REFERENCES "songData" ("songId"),
    FOREIGN KEY ("userId") REFERENCES "userData" ("userId"),
    CHECK ("isLike" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "songPlays" (
    "songId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "playCount" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("songId", "userId"),
    FOREIGN KEY ("songId") REFERENCES "songData" ("songId"),
    FOREIGN KEY ("userId") REFERENCES "userData" ("userId")
);

CREATE TABLE IF NOT EXISTS "songComments" (
    "songId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "comment" TEXT NOT NULL,
    "redFlagCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("songId", "userId"),
    FOREIGN KEY ("songId") REFERENCES "songData" ("songId"),
    FOREIGN KEY ("userId") REFERENCES "userData" ("userId"),
    CHECK ("isFlagged" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "albumSongs" (
    "albumId" INTEGER NOT NULL,
    "songId" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY ("albumId") REFERENCES "albumData" ("albumId"),
    FOREIGN KEY ("songId") REFERENCES "songData" ("songId"),
    PRIMARY KEY ("albumId", "songId")
);

CREATE TABLE IF NOT EXISTS "playlistData" (
    "playlistId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "playlistName" TEXT NOT NULL,
    "playlistDescription" TEXT NULL,
    "userId" INTEGER NOT NULL,
    "isPublic" TEXT NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastUpdatedAt" TEXT NULL,
    FOREIGN KEY ("userId") REFERENCES "userData" ("userId"),
    CHECK ("isPublic" IN ("0", "1"))
);

CREATE TABLE IF NOT EXISTS "playlistSongs" (
    "playlistId" INTEGER NOT NULL,
    "songId" INTEGER NOT NULL,
    "createdAt" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY ("playlistId") REFERENCES "playlistData" ("playlistId"),
    FOREIGN KEY ("songId") REFERENCES "songData" ("songId"),
    PRIMARY KEY ("playlistId", "songId")
);

INSERT INTO "userRole" ("roleName") VALUES ("ADMIN");
INSERT INTO "userRole" ("roleName") VALUES ("CREATOR");
INSERT INTO "userRole" ("roleName") VALUES ("USER");

INSERT INTO "userData" ("userName", "userEmail", "userPassword", "userRoleId", "userDob", "userGender", "accountStatus") VALUES ("Admin", "admin@gmail.com", "admin123", "0", "2002-01-01", "M", "1");



INSERT INTO "languageData" ("languageName") VALUES ("English");
INSERT INTO "languageData" ("languageName") VALUES ("Hindi");
INSERT INTO "languageData" ("languageName") VALUES ("Tamil");
INSERT INTO "languageData" ("languageName") VALUES ("Telugu");
INSERT INTO "languageData" ("languageName") VALUES ("Malayalam");
INSERT INTO "languageData" ("languageName") VALUES ("Kannada");
INSERT INTO "languageData" ("languageName") VALUES ("Spanish");


INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Classical", "Classical music is art music produced or rooted in the traditions of Western culture, including both liturgical (religious) and secular music.", "1", 1);
INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Country", "Country music, also known as country and western (or simply country), and hillbilly music, is a genre of popular music that takes its roots from genres such as blues and old-time music, and various types of American folk music including Appalachian, Cajun, and the cowboy Western music styles of Red Dirt, New Mexico, Texas country, and Tejano.", "1", 1);
INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Folk", "Folk music includes traditional folk music and the genre that evolved from it during the 20th-century folk revival.", "1", 1);
INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Melody", "Melody is a linear sequence of notes the listener hears as a single entity. The term comes from the Greek word melōidía and is used by Plato and Aristotle to describe music of any kind, including music of the spheres and music played by the Muses.", "1", 1);
INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Rock", "Rock is a genre of popular music that originated as 'rock and roll' in the United States in the 1950s, and developed into a range of different styles in the 1960s and later, particularly in the United States and the United Kingdom.", "1", 1);
INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Pop", "Pop is a genre of popular music that originated in its modern form during the mid-1950s in the United States and the United Kingdom.", "1", 1);
INSERT INTO "genreData" ("genreName", "genreDescription", "isActive", "createdBy") VALUES ("Jazz", "Jazz is a music genre that originated in the African-American communities of New Orleans, Louisiana, United States, in the late 19th and early 20th centuries, with its roots in blues and ragtime.", "1", 1);
"""

def reinitializeDatabase():
    try:
        db_connection = sqlite3.connect('./schema/app_data.db')
        db_cursor = db_connection.cursor()
        db_cursor.executescript(init_query)
        db_connection.commit()
        db_connection.close()

        print("[MESSAGE]: Database reinitialized successfully.")
    except Exception as e:
        f = open("logs/errorLogs.txt", "a")
        f.write(f"[ERROR] {datetime.now()}: {e}\n")
        f.close()
        print("[ERROR]: Error in reinitializing database.")
    finally:
        return
    
def initEnvironment():
    # Clear files
    f = open("logs/errorLogs.txt", "w")
    f.write("")
    f.close()

    print("[MESSAGE]: Error logs cleared")

    # Clear all files under static/music
    for file in os.listdir('static/music/song'):
        os.remove(f"static/music/song/{file}")

    for file in os.listdir('static/music/poster'):
        os.remove(f"static/music/poster/{file}")

    for file in os.listdir('static/music/album'):
        os.remove(f"static/music/album/{file}")

    print("[MESSAGE]: Music files cleared")

    return