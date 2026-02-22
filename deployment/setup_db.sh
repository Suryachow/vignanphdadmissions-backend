#!/bin/bash
# --- AWS EC2 DATABASE INSTANCE SETUP (Ubuntu 22.04) ---
# TARGET: Instance 3 (Vault)

# 1. Update and Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# 2. Configure PostgreSQL to allow remote connections
# Change listen_addresses to '*' to allow the backend to connect
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf

# 3. Add Backend Instance IP to allowed hosts (Security)
# REPLACE <BACKEND_PRIVATE_IP> with the actual Private IP of Instance 2
echo "host    phd_admissions    postgres    <BACKEND_PRIVATE_IP>/32    md5" | sudo tee -a /etc/postgresql/14/main/pg_hba.conf

# 4. Restart Service
sudo systemctl restart postgresql

# 5. Create Database and User
# Change '9989' to your desired secure production password
sudo -u postgres psql -c "CREATE DATABASE phd_admissions;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '9989';"

echo "✅ Database Instance Setup Complete!"
echo "⚠️ REMINDER: Open Port 5432 in AWS Security Group for the Backend Instance IP."
