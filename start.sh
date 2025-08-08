#!/bin/bash

echo "Starting Audio to MIDI Converter..."
echo

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo
echo "Installing Node.js dependencies..."
npm install

echo
echo "Starting backend server..."
python server.py &
BACKEND_PID=$!

echo
echo "Waiting for backend to start..."
sleep 3

echo
echo "Starting frontend server..."
npm start &
FRONTEND_PID=$!

echo
echo "Both servers are starting..."
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo
echo "Press Ctrl+C to stop both servers..."

# Wait for user to stop
wait 