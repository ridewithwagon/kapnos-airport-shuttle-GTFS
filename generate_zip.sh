python3 generate.py
wget -O osm/cyprus-latest.osm.bz2 https://download.geofabrik.de/europe/cyprus-latest.osm.bz2
docker pull ghcr.io/ad-freiburg/pfaedle:latest
docker run -i --rm \
    --volume "$(pwd)/osm:/osm" \
    --volume "$(pwd)/GTFS.zip:/gtfs/myfeed.zip" \
    --volume "$(pwd)/output:/gtfs-out" \
    ghcr.io/ad-freiburg/pfaedle:latest \
    -x /osm/cyprus-latest.osm.bz2 -i /gtfs/myfeed.zip
rm gtfs.zip
rm -f output.zip
zip -j output.zip output/*.txt