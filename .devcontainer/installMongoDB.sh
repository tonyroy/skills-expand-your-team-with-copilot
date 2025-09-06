#!/bin/bash


# Install MongoDB (updated for GPG key verification)
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Create necessary directories and set permissions
sudo mkdir -p /data/db
sudo chown -R mongodb:mongodb /data/db

# Start MongoDB service
sudo mongod --fork --logpath /var/log/mongodb/mongod.log

echo "MongoDB has been installed and started successfully!"
mongod --version

# Run sample MongoDB commands
echo "Current databases:"
mongosh --eval "db.getMongo().getDBNames()"