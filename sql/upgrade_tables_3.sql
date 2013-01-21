USE mowmow;

CREATE TABLE users(
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(70) NOT NULL,
    email VARCHAR(70) NOT NULL,
    pass_hash VARCHAR(100) NOT NULL,
    privilege INT NOT NULL,
    time_stamp TIMESTAMP
);

CREATE TABLE user_tokens(
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(100) NOT NULL,
    time_stamp TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO users (name,email,pass_hash,privilege) VALUES (
    "Unknown",
    "unknown",
    "none",
    0
);

ALTER TABLE nomnoms DROP user_name;
ALTER TABLE nomnoms ADD user_id INT NOT NULL;
UPDATE nomnoms SET user_id=1, time_stamp=time_stamp;
ALTER TABLE nomnoms ADD FOREIGN KEY (user_id) REFERENCES users(id);
