[![CI/CD Pipeline](https://github.com/software-students-spring2024/5-final-project-spring-2024-ai-ja/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/software-students-spring2024/5-final-project-spring-2024-ai-ja/actions/workflows/ci-cd.yml)

# Final Project

# Project Description
This project utilizes ML to estimate the age, gender, race, and dominant emotion of the user. Through the web app, a user can upload their photo to be analyzed. The user can then view their results and a generated message related to their analysis.

# How to run

Our project is currently deployed [here](http://143.198.20.243:5002/) --> http://143.198.20.243:5002/

If not using the deployed link, this app can be run through Docker Desktop. If you need to install Docker, you can create an account and download it [here](https://www.docker.com/products/docker-desktop/).

Create a local repository using the following command:
    
    git clone https://github.com/software-students-spring2024/5-final-project-spring-2024-ai-ja.git

After navigating to the local repository, run the following command (you must ensure that Docker Desktop is running).

    docker-compose down

To install the required dependencies and run the program, run the following command. Once the required dependencies have been installed the first time, the command can be run without the --build tag.

    docker-compose up --build

To use the app, open a web browser and navigate to [localhost:5002](http://localhost:5002/).

# Starter Data

No starter data is required.

# Contributors

- [Alex Kondratiuk](https://github.com/ak8000)
- [Janet Pan](https://github.com/jp6024)
- [Adam Schwartz](https://github.com/aschwartz01)
