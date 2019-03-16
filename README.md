# Flask Blog

Beacuse life is short, use Python

### Cloud Datastore Implementation

Not this branch supports Cloud DataStore. If you need it deployed on Cloud SQL refer to Master Branch.

### Demo running at

http://cloud-datastore-alpha.appspot.com/

### Complete Blog Post 

https://medium.com/@zainqasmi/build-and-deploy-a-python-flask-application-on-google-cloud-using-app-engine-and-cloud-sql-a3c5bde5ef4a

### Prerequisites

* Python 2.7.15

* Install packages in requirements.txt
```
pip install -r requirements.txt
```


## Getting Started

### To run on localhost:
    
* Need to have Google Cloud SDK installed
* Run
    ```
    dev_appserver.py app.yaml
    ```

### To deploy on gcloud app engine:
* Run
    ```
    gcloud app deploy
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