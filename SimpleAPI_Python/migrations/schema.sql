-- 1. Create and use the database
CREATE DATABASE IF NOT EXISTS simple_pins_api;
USE simple_pins_api;

-- 2. Create the User table (Parent Table)
CREATE TABLE User (
    UserUUID BINARY(16) PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Password CHAR(60) NOT NULL
);

-- 3. Create the RefreshToken table (Child Table)
CREATE TABLE RefreshToken (
    TokenID INT AUTO_INCREMENT PRIMARY KEY,
    UserUUID BINARY(16) NOT NULL,
    Token VARCHAR(512) NOT NULL UNIQUE,
    ExpiresAt DATETIME NOT NULL,
    IsRevoked BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (UserUUID) REFERENCES User(UserUUID) ON DELETE CASCADE
);

-- 4. Create the Pin table (Child Table)
CREATE TABLE Pin (
    PinID INT AUTO_INCREMENT PRIMARY KEY,
    UserUUID BINARY(16) NOT NULL,
    PinTitle VARCHAR(255) NOT NULL,
    PinBody TEXT,
    ImageLink VARCHAR(2048),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserUUID) REFERENCES User(UserUUID) ON DELETE CASCADE
);
