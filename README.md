# Flask App

Beacuse life is short, use Python

### Prerequisites

Python 2.7.15

Install packages in requirements.txt
```
pip install -r requirements.txt
```

Configure cloud_sql_instance name in app.yaml:
```
beta_settings:
  cloud_sql_instances: project-name:region-name:instance-name
```

Configure database credentials:
```
app.config['MYSQL_UNIX_SOCKET'] = "/cloudsql/project-name:region-name:instance-name"
app.config['MYSQL_USER'] = database username
app.config['MYSQL_PASSWORD'] = database user password
app.config['MYSQL_DB'] = database name
```

## Getting Started

To run on localhost:
    
    * Comment out line 13 in main.py
    ```
    appengine.monkeypatch()
    ```
    * Configure SQL connection:
    ```
    app.config['MYSQL_HOST'] = localhost
    ```
    * Run
    ```
    python main.py
    ```

To deploy on gcloud app engine:
    * Run
    ```
    gcloud app deploy
    ```
To enable login via Facebook or Google:
    ```
    app.config["GOOGLE_OAUTH_CLIENT_ID"] = Add google client API key
    app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = Add google client secret API key
    app.config["FACEBOOK_OAUTH_CLIENT_ID"] = Add google client API key
    app.config["FACEBOOK_OAUTH_CLIENT_SECRET"] = Add google client secret API key
    ```

## Running the tests

* Run
```
python flaskunitests.py
```

## Built With

* [Python Flask](http://flask.pocoo.org/)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details