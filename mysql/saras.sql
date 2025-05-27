CREATE DATABASE STOCKMARKET_PROJECT;
USE STOCKMARKET_PROJECT;

-- User table to store authentication information
CREATE TABLE user (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    account_status ENUM('active', 'suspended', 'inactive') DEFAULT 'active'
);
SELECT * FROM user;

-- Admin table for system administrators
CREATE TABLE admin (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    admin_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
SELECT * FROM admin;


CREATE TABLE stock (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    current_price DECIMAL(10, 2),
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    volume BIGINT,
    change_percentage DECIMAL(5, 2),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

SELECT * FROM stock;

-- Watchlist table (user-specific stock selections)
CREATE TABLE watchlist (
    watchlist_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    stock_symbol VARCHAR(20) NOT NULL,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_stock (user_id, stock_symbol)
);
SELECT * FROM watchlist;

-- Portfolio table (user's holdings)
CREATE TABLE portfolio (
    portfolio_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    stock_symbol VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    purchase_price DECIMAL(10, 2) NOT NULL,
    purchase_date DATE NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);
SELECT * FROM portfolio;


-- Analytics preferences (user's preferred stocks for analysis)
CREATE TABLE analytics_preferences (
    preference_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    stock_symbol VARCHAR(20) NOT NULL,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_analysis (user_id, stock_symbol)
);
SELECT * FROM analytics_preferences;


-- Access logs for security and monitoring
CREATE TABLE access_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    admin_id INT,
    action_type VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    status VARCHAR(20),
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE SET NULL,
    FOREIGN KEY (admin_id) REFERENCES admin(admin_id) ON DELETE SET NULL
);
SELECT * FROM access_logs;

-- Simplified company reports table without description
-- Minimalist company reports table
CREATE TABLE company_reports (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    stock_symbol VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(100) NOT NULL,
    current_price DECIMAL(10, 2),
    market_cap DECIMAL(20, 2),
    report_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM company_reports;

-- Simple User Report Table that only stores ID, username, and email
CREATE TABLE admin_reports (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    report_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);
SELECT * FROM admin_reports;

-- Add index for better performance
ALTER TABLE user_reports ADD INDEX idx_user_id (user_id);
ALTER TABLE user_reports ADD INDEX idx_report_date (report_date);

-- Example data insertion
INSERT INTO user_reports (user_id, user_name, email) 
SELECT user_id, user_name, email FROM user;

-- Add index in a separate statement if needed
ALTER TABLE company_reports ADD INDEX idx_stock (stock_symbol);
SELECT * FROM company_reports;

-- Add indexes for better performance
ALTER TABLE watchlist ADD INDEX idx_user_id (user_id);
ALTER TABLE portfolio ADD INDEX idx_user_id (user_id);
ALTER TABLE analytics_preferences ADD INDEX idx_user_id (user_id);
ALTER TABLE analysis_notes ADD INDEX idx_user_id (user_id);
ALTER TABLE access_logs ADD INDEX idx_timestamp (timestamp);
INSERT INTO admin (admin_name, email, password) 
VALUES ('admin', 'admin@sarasfintech.com', 'admin123');

-- Drop the tables you don't want
DROP TABLE IF EXISTS analysis_notes;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS user_dashboard_settings;