CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    password VARCHAR(100)
);

INSERT INTO users (username, email, password) VALUES
    ('alice', 'alice@test.org', '12345'),
    ('bob1', 'bob@test.org', 'abcde')
ON CONFLICT DO NOTHING;
