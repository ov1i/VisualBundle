#!/bin/bash

# Function to update deps, install python3-venv and ensure pip is installed
install_venv() {
   # sudo apt-get update
    sudo apt-get install -y python3-pip
    sudo apt-get install -y python3-venv
}

# Function to create a virtual environment
create_virtualenv() {
    local env_name=$1
    python3 -m venv "$env_name"
}

activate_virtualenv() {
    local env_name=$1
    source $env_name/bin/activate
}

install_dependencies() {
    pip install -r "dependencies/requirements.txt"
}

# Main script
main() {
    local env_name=".venv"

    # Install python3-venv
    install_venv

    # Create the virtual environment
    echo "Creating the virtual environment"
    create_virtualenv "$env_name"
    echo "Virtual environment '$env_name' created successfully."

    # Activate the virtual environment
    echo "Activating the virtual environment"
    activate_virtualenv "$env_name"
    echo "Virtual environment '$env_name' activated successfully."

    echo "Installing into the virtual environment dependencies from /dependencies/requirements.txt"
    install_dependencies
    echo "Dependencies installed into the environment '$env_name' successfully."

}

# Call the main function
main
