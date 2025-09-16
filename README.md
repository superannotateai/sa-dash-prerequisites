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
# Code to be used in vis.py

## For Plotly items:
```python
if __name__ == "__main__":
    import os
    from snap import snap_plotly_and_map

    output_dir = os.environ.get("DASH_OUTPUT_PATH", ".")

    fig = data_visualizer("data.json")

    # Export the Plotly figure as a static HTML file
    html_path = os.path.join(output_dir, "output.html")
    fig.write_html(html_path, full_html=True, include_plotlyjs=True)
    print(f"Static HTML exported to {html_path}")

    # Export screenshot
    screenshot_path = snap_plotly_and_map(html_path)
    print(f"Screenshot saved to: {screenshot_path}")
```

## For Map items:
```python
if __name__ == "__main__":
    from snap import map_export_html, snap_plotly_and_map

    # Get the rturned fig object from data_vsiualizer
    fig = data_visualizer("data.json")

    # Export files
    html_path = map_export_html(fig, output_dir)
    print(f"Homepage HTML exported to {html_path}")

    screenshot_path = snap_plotly_and_map(html_path)
    print(f"Screenshot saved to: {screenshot_path}")
```

## For Dash items:
```python
if __name__ == "__main__":
    import os
    from snap import dash_export_html, snap_dash

    output_dir = os.environ.get("DASH_OUTPUT_PATH", ".")
    
    # Get the Dash app
    app = data_visualizer("data.json")
    
    # Export HTML
    html_path = dash_export_html(app, output_dir)
    print(f"Homepage HTML exported to {html_path}")

    # Export Screenshot
    screenshot_path = snap_dash(html_path)
    print(f"Screenshot saved to: {screenshot_path}")
```
