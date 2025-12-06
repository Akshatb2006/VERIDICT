#!/bin/bash

# Sentenex Project Setup Script
# This script helps set up the Sentenex project with proper dependency management

echo "========================================="
echo "Sentenex Project Setup"
echo "========================================="
echo ""

# Get the directory where the script is located
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $PROJECT_DIR"
echo ""

# Option menu
echo "Select setup option:"
echo "1. Quick setup (install with --break-system-packages)"
echo "2. Recommended setup (create venv in home directory)"
echo "3. Move project to ~/sentenex (recommended for long-term)"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "Installing dependencies with --break-system-packages..."
    cd "$PROJECT_DIR"
    pip3 install -r requirements.txt --break-system-packages
    
    if [ $? -eq 0 ]; then
      echo ""
      echo "✅ Dependencies installed successfully!"
      echo ""
      echo "To start the server, run:"
      echo "  cd \"$PROJECT_DIR\""
      echo "  python3 app.py"
    else
      echo "❌ Installation failed. Please check the errors above."
      exit 1
    fi
    ;;
    
  2)
    echo ""
    echo "Creating virtual environment in home directory..."
    cd ~
    python3 -m venv sentenex_venv
    
    echo "Activating virtual environment..."
    source ~/sentenex_venv/bin/activate
    
    echo "Installing dependencies..."
    cd "$PROJECT_DIR"
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
      echo ""
      echo "✅ Setup complete!"
      echo ""
      echo "To start the server:"
      echo "  1. Activate the virtual environment:"
      echo "     source ~/sentenex_venv/bin/activate"
      echo "  2. Navigate to project:"
      echo "     cd \"$PROJECT_DIR\""
      echo "  3. Start the server:"
      echo "     python app.py"
    else
      echo "❌ Installation failed. Please check the errors above."
      exit 1
    fi
    ;;
    
  3)
    echo ""
    echo "Moving project to ~/sentenex..."
    
    # Check if ~/sentenex already exists
    if [ -d ~/sentenex ]; then
      echo "⚠️  Directory ~/sentenex already exists!"
      read -p "Do you want to remove it and continue? (y/n): " confirm
      if [ "$confirm" != "y" ]; then
        echo "Setup cancelled."
        exit 0
      fi
      rm -rf ~/sentenex
    fi
    
    # Move project
    mv "$PROJECT_DIR" ~/sentenex
    cd ~/sentenex
    
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
      echo ""
      echo "✅ Setup complete!"
      echo ""
      echo "Your project has been moved to: ~/sentenex"
      echo ""
      echo "To start the server:"
      echo "  1. Navigate to project:"
      echo "     cd ~/sentenex"
      echo "  2. Activate the virtual environment:"
      echo "     source venv/bin/activate"
      echo "  3. Start the server:"
      echo "     python app.py"
    else
      echo "❌ Installation failed. Please check the errors above."
      exit 1
    fi
    ;;
    
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
