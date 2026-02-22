#!/bin/bash
# --- AWS EC2 BACKEND INSTANCE SETUP (Ubuntu 22.04) ---
# TARGET: Instance 2 (Logic)

# 1. Update and Install Python
sudo apt update
sudo apt install python3-pip python3-venv git -y

# 2. Clone Repository (You will need to push your code to GitHub first)
# git clone <YOUR_REPO_URL> backend
# cd backend

# 3. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Dependencies
pip install -r requirements.txt
pip install gunicorn  # Recommended for production

# 5. Create Systemd Service (To keep the app running forever)
sudo bash -c 'cat > /etc/systemd/system/vignan-backend.service <<EOF
[Unit]
Description=Gunicorn instance to serve Vignan PhD Backend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/backend
Environment="PATH=/home/ubuntu/backend/venv/bin"
ExecStart=/home/ubuntu/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
EOF'

# 6. Start the service
sudo systemctl start vignan-backend
sudo systemctl enable vignan-backend

echo "✅ Backend Instance Setup Complete!"
