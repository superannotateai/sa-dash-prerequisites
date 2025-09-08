# Running via Docker
## To create the chart

```sh
docker build -t "chart_creation" .
docker run --network none --rm -e DASH_OUTPUT_PATH="output" -v "$PWD/output_from_docker:/app/output" chart_creation
```

## To verify the output
```sh
open output_from_docker/output.html
open output_from_docker/screenshot.png
```

# Running via Python
## Installation
```sh
pip3 install -r requirements.txt
plotly_get_chrome -y

# Get all the topology files
mkdir topojson
cd topojson

# Download the latest version of the topology files
curl -s https://api.github.com/repos/plotly/plotly.js/contents/dist/topojson | jq -r '.[].download_url' | xargs -n 1 curl -O
```

## To create the chart
```sh
python3 gen.py && python3 vis.py
```

## To verify the output
```sh
open output.html
open screenshot.png
```