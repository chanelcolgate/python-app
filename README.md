### README

This directory contains the source code for the third exercise of chapter 4. In this exercise, we compose a Dockerfile for Newsbot and then use the Dockerfile to build a Docker image and run the container.

#### Reddit
You need to make sure that you have set up a Reddit app on the Reddit website and obtained the necessary authentication details, including the `client_id`. Here are the steps to do that:
1. **Create a Reddit App**:
- Go to the [Reddit Developer](https://www.reddit.com/prefs/apps/)
- Scroll down to the "Developer Applications" section.
- Click on the "Create App" or "Create Another App" button.
- Fill in the required fields, including the name, app type (script, web app, etc.), and description. For a simple script, you can choose "script"
- Set the "permissions" to the minimum required for your application.
- Set the "redirect URI" to "http://localhost:8080" (this is for script-type apps)
- Click on the "Create app" button.
2. **Retrieve 'client_id'**
- After creating the app, you will be redirected to the app details page.
- Find the 'client_id' on this page. It should look like a random string of characters.
3. **Update Your PRAW Script**
- In your PRAW script, make sure you are initializing the Reddit instance with the correct credentials, including 'client_id'
- Here's an example of how you might initialize PRAW with your credentials:
```python
import praw

reddit = praw.Reddit(
    client_id='your_client_id',
    client_secret='your_client_secret',
    user_agent='your_user_agent',
)

```
#### Building the Docker image
Build the image using the below command
```
docker build -t chanelcolgate/newsbot .
```
Run the container using
```
docker run -e NBT_ACCESS_TOKEN=<token> chanelcolgate/newsbot
```
Replace `<token>` with the Telegram API Token that was generated.

#### How to run docker-compose.yaml
Step 1: Create folder `images` and folder `tmp`
Step 2: Fill path folder `images` and `tmp` into docker-compose in service `main`
Step 3:
```
docker-compose up -d bentoml
```
Step 4:
```
docker-compose up -d db
```
Step 5:
```
docker-compose up -d adminer
```
Step 6:
```
docker-compose up -d rabbitmq
```
Step 7:
```
docker-compose up -d declare
```
Step 8:
```
docker-compose up -d --scale worker=3
```
Step 9:
```
docker-compose up -d main
```
Step 10:
```
docker-compose up -d webserver
```

### Debezium
The pgoutput plugin is built into PostgreSQL and requires no additional installation.
```
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  postgres:15 \
  -c wal_level=logical \
  -c max_replication_slots=10 \
  -c max_wal_senders=10 \
  -c shared_preload_libraries='pgoutput'

```
In your Debezium connector configuration, specify the pgoutput plugin:
```json
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.hostname": "postgres",
  "database.port": 5432,
  "database.user": "postgres",
  "database.password": "postgres",
  "database.dbname": "postgres",
  "slot.name": "debezium_slot",
  "publication.autocreate.mode": "filtered",
  "plugin.name": "pgoutput"
}

```
- Create
```
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json"  http://localhost:8083/connectors -d @register-postgres.json
```
- Update
```
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json"  http://localhost:8083/connectors/postgres/config -d @register-postgres.json
```
- Restart
```
curl -X POST http://localhost:8083/connectors/{connector-name}/restart
```
- Delete
```
curl -i -X DELETE -H "Accept:application/json" -H "Content-Type:application/json"  http://localhost:8083/connectors/postgres22
```