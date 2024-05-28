BEGIN TRANSACTION;
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
INSERT INTO "users" VALUES(1,'Admin','User','cerenaydinn00@gmail.com','1234','admin');
INSERT INTO "users" VALUES(2,'Admin','User','ydnceren00@gmail.com','123','admin');
INSERT INTO "users" VALUES(3,'ceren','aydýn','ceren.aydin@ozan','12','user');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('users',3);
COMMIT;
