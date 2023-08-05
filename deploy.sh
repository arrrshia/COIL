#!/bin/bash

# Function to read username and password arguments
read_arguments() {
    # Check if both arguments are provided
    if [ $# -ne 2 ]; then
        echo "Error: Please provide both username and password arguments"
        exit 1
    fi
    
    # Assign arguments to variables
    username=$1
    password=$2
    
    # Print the username and password
    export username=$username
    export password=$password
}

# Wait for five seconds
sleep 5

# Call the function with the provided arguments
read_arguments "$@"

docker compose up -d