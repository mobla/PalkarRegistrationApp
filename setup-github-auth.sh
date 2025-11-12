#!/bin/bash

echo "🔧 GitHub Authentication Setup Script"
echo "------------------------------------"
echo "Choose authentication method:"
echo "1) HTTPS (Personal Access Token)"
echo "2) SSH (Recommended for long-term use)"
read -p "Enter choice [1 or 2]: " choice

if [ "$choice" == "1" ]; then
    echo ""
    echo "🌐 Setting up HTTPS (Token-based authentication)"
    read -p "Enter your GitHub username: " ghuser
    read -p "Enter your GitHub repository URL (e.g. https://github.com/user/repo.git): " ghurl
    git remote set-url origin "$ghurl"

    echo ""
    echo "🪪 Please go to https://github.com/settings/tokens → Generate new token (classic)"
    echo "   → Select 'repo' scope, then copy the token."
    echo ""
    echo "After this, when prompted for password during 'git push', paste your token."
    git config --global credential.helper store
    echo "✅ Token will be saved after first push."
    echo ""
    echo "Try running: git push -u origin main"
    
elif [ "$choice" == "2" ]; then
    echo ""
    echo "🔑 Setting up SSH authentication"
    read -p "Enter your GitHub email (used for account): " ghemail

    # Generate SSH key
    ssh-keygen -t ed25519 -C "$ghemail"

    # Start ssh-agent
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519

    # Show key for GitHub setup
    echo ""
    echo "📋 Copy the key below and add it to GitHub → Settings → SSH and GPG keys → New SSH key:"
    echo "----------------------------------------------------------------------------------------"
    cat ~/.ssh/id_ed25519.pub
    echo "----------------------------------------------------------------------------------------"

    read -p "Press Enter after adding the key on GitHub..."

    # Replace HTTPS remote with SSH
    read -p "Enter your GitHub repository SSH URL (e.g. git@github.com:user/repo.git): " sshurl
    git remote set-url origin "$sshurl"

    echo "✅ SSH setup complete! Try pushing now:"
    echo "   git push -u origin main"
else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi
