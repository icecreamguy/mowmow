USE mowmow;

DROP TABLE IF EXISTS photo;
DROP TABLE IF EXISTS nomnoms;

CREATE TABLE nomnoms(
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    time_stamp TIMESTAMP
);

CREATE TABLE photo(
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    file_path VARCHAR(30),
    file_name VARCHAR(30),
    nomnom_id INT,
    INDEX nomnom_index (nomnom_id),
    FOREIGN KEY (nomnom_id) REFERENCES nomnoms(id) ON DELETE CASCADE
);
