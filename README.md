# Homes

App to manage Point of Interest Locations. 

The App built with Python, Django.

Uses PostgreSQL database with Postgis extension for geospatial data.

---
### Prerequisites

Requires a local docker installation.

## Local Environment.

Clone the repository
<pre>
git clone https://github.com/peterwade153/homes.git
</pre>

- Start the Docker deamon on the machine if its not running already.

- Switch to the homes directory.

To start the app
<pre>
docker-compose up
</pre>


## Testing Data Import

To import data for the supported file formats. There are sample files that are included in the sample_date folder.

- To run the import command. Open a new terminal in the homes directory and run the command below.

For directories.
<pre>
docker exec -it app python manage.py import sample_data/
</pre>

For a single file.
<pre>
docker exec -it app python manage.py import sample_data/pois.csv
</pre>


## Accessing the Admin dash

Create a super user account
<pre>
docker exec -it app python manage.py createsuperuser
</pre>

Access the dashboard with link below
<pre>
http://localhost:8000/admin
</pre>


** There are project notes in the Notes.txt, file included in the repo.