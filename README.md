**NOTE:**  This app is not currently not deployed so to run need to build locally.I generalized the CI/CD pipeline file (changing Docker username there to just 'username', so if your want to clone it and deploy on Digital Ocean or somewhere else, make sure to add your username there, and create an env with OPENAI API Key, Secret Key, and also add them to your repo secrets on github along with DOCKERHUB username and token

# Project Description
This was my team project for a Software Engineering class at NYU. It is a containerized webapp that utilizes deepface ML to estimate the age, gender, race, and dominant emotion of the user. Through the web app, a user can upload their photo to be analyzed. The user can then view their results and a generated message related to their analysis.

# How to run

This app can be run through Docker Desktop. If you need to install Docker, you can create an account and download it [here](https://www.docker.com/products/docker-desktop/).

Create a local repository using the following command:
    
    git clone https://github.com/ak8000/deployable-age-recognizer-web-app.git

After navigating to the local repository, run the following command (you must ensure that Docker Desktop is running).

    docker-compose down

To install the required dependencies and run the program, run the following command. Once the required dependencies have been installed the first time, the command can be run without the --build tag.

    docker-compose up --build

To use the app, open a web browser and navigate to [localhost:5002](http://localhost:5002/).

# Contributors

- [Alex Kondratiuk](https://github.com/ak8000)
- [Janet Pan](https://github.com/jp6024)
- [Adam Schwartz](https://github.com/aschwartz01)
