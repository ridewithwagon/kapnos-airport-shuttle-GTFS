# generate default zip file
python3 generate.py

# add shapes and generate new zip file
wget -O osm/cyprus-latest.osm.bz2 https://download.geofabrik.de/europe/cyprus-latest.osm.bz2
docker pull ghcr.io/ad-freiburg/pfaedle:latest
docker run -i --rm \
    --volume "$(pwd)/osm:/osm" \
    --volume "$(pwd)/GTFS.zip:/gtfs/myfeed.zip" \
    --volume "$(pwd)/output:/gtfs-out" \
    ghcr.io/ad-freiburg/pfaedle:latest \
    -x /osm/cyprus-latest.osm.bz2 -i /gtfs/myfeed.zip

# unzip fare_attributes.txt and fare_rules.txt from gtfs.zip
unzip gtfs.zip -d gtfs

# replace fare_attributes.txt and fare_rules.txt in output folder
cp gtfs/fare_attributes.txt output/fare_attributes.txt
cp gtfs/fare_rules.txt output/fare_rules.txt

# remove tmp folders
rm -f output.zip
rm -f gtfs.zip
rm -rf gtfs

zip -j output.zip output/*.txt