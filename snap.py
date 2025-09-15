from playwright.sync_api import sync_playwright
import threading
import time
import os
import json

import socketserver
from http.server import SimpleHTTPRequestHandler


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=kwargs.pop('directory', '.'), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()


def start_server(directory, port):
    """Start HTTP server in a separate thread"""
    def run_server():
        handler = lambda *args, **kwargs: CORSRequestHandler(*args, directory=directory, **kwargs)
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread


def map_export_html(fig, output_dir, topojson_dir="topojson"):
    # 1. Start topojson server
    start_server(topojson_dir, 8080)
    
    # 2. Generate initial HTML
    os.makedirs(output_dir, exist_ok=True)
    temp_html_path = os.path.join(output_dir, "temp_output.html")
    
    fig.write_html(
        temp_html_path,
        full_html=True,
        include_plotlyjs=True,
        config={'topojsonURL': 'http://localhost:8080/'}
    )
    
    # 3. Start HTML server
    start_server(output_dir, 8090)
    time.sleep(3)
    
    # 4. Capture requests and rendered HTML
    topojson_data = {}
    
    with sync_playwright() as p:
        browser, page = _get_browser_page(p)
        
        # Intercept topojson requests
        def handle_response(response):
            if 'localhost:8080' in response.url and response.url.endswith('.json'):
                filename = response.url.split('/')[-1]
                try:
                    topojson_data[filename] = response.json()
                    print(f"Captured: {filename}")
                except Exception as e:
                    print(f"Failed to capture {filename}: {e}")
        
        page.on('response', handle_response)
        
        # Load the page and wait for everything
        page.goto('http://localhost:8090/temp_output.html')
        page.wait_for_selector('.plotly-graph-div', timeout=30000)  # 30s for loading plotly graph with map
        try:
            # Trying domcontentloaded (less strict than networkidle)
            page.wait_for_load_state('domcontentloaded', timeout=10000) # more 10s wait if 30s is not enough
            print("DOM content loaded")
            
            # wait for networkidle with longer timeout
            page.wait_for_load_state('networkidle', timeout=45000)  # wait 45s
            print("Network idle achieved")
            
        except Exception as e:
            print(f"Wait state timeout ({e}), proceeding anyway...")
            page.wait_for_timeout(10000)

        # Additional wait to ensure Plotly has finished rendering
        print("Waiting for final rendering...")
        page.wait_for_timeout(5000)
        
        # Get the fully rendered HTML
        html_content = page.content()
        browser.close()
    
    # 5. Create static version with embedded data
    if topojson_data:
        print(f"Embedding {len(topojson_data)} topojson files...")
        
        # Create a mapping of topojson data
        data_map = {}
        for filename, data in topojson_data.items():
            data_map[filename] = data
        
        # Inject JavaScript to override topojson fetching
        embed_script = f"""
        <script>
        // Embedded topojson data
        window.EMBEDDED_TOPOJSON = {json.dumps(data_map)};
        
        // Override XMLHttpRequest for topojson requests
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url, ...args) {{
            this._url = url;
            return originalXHROpen.call(this, method, url, ...args);
        }};
        
        XMLHttpRequest.prototype.send = function(data) {{
            if (this._url && this._url.includes('localhost:8080')) {{
                const filename = this._url.split('/').pop();
                if (window.EMBEDDED_TOPOJSON[filename]) {{
                    console.log('Using embedded topojson:', filename);
                    
                    // Simulate successful response
                    setTimeout(() => {{
                        Object.defineProperty(this, 'status', {{ value: 200, writable: false }});
                        Object.defineProperty(this, 'statusText', {{ value: 'OK', writable: false }});
                        Object.defineProperty(this, 'responseText', {{ 
                            value: JSON.stringify(window.EMBEDDED_TOPOJSON[filename]), 
                            writable: false 
                        }});
                        Object.defineProperty(this, 'readyState', {{ value: 4, writable: false }});
                        
                        if (this.onreadystatechange) {{
                            this.onreadystatechange();
                        }}
                        if (this.onload) {{
                            this.onload();
                        }}
                    }}, 0);
                    return;
                }}
            }}
            return originalXHRSend.call(this, data);
        }};
        </script>
        """
        
        # Insert the script before </head>
        html_content = html_content.replace('</head>', f'{embed_script}\n</head>')
    
    # 6. Save final HTML
    final_html_path = os.path.join(output_dir, "output.html")
    with open(final_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Cleanup
    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)
    
    return final_html_path



def _get_browser_page(p):
    """Create browser and page with standard viewport"""
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    return browser, page


def dash_export_html(app, output_dir):
    
    def run_app():
        app.run(debug=False, port=8050, host='127.0.0.1', use_reloader=False)
    
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()
    time.sleep(3)
    
    with sync_playwright() as p:
        browser, page = _get_browser_page(p)
        
        # Navigate to app
        page.goto('http://127.0.0.1:8050')
        page.wait_for_selector('#react-entry-point', timeout=10000)
        page.wait_for_timeout(5000)

        html_content = page.content()
        css_content = page.evaluate("""
        () => {
            let css = '';
            for (let sheet of document.styleSheets) {
                try {
                    for (let rule of sheet.cssRules) {
                        css += rule.cssText + '\\n';
                    }
                } catch (e) {}
            }
            return css;
        }
        """)
        
        css_tag = f'<style>\n{css_content}\n</style>'
        html_content = html_content.replace('</head>', f'{css_tag}\n</head>')
        
        os.makedirs(output_dir, exist_ok=True)
        html_path = os.path.join(output_dir, "output.html")

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        browser.close()

        return html_path



def snap_plotly_and_map(html_file_path, output_path="output/screenshot.png"):
    with sync_playwright() as p:
        browser, page = _get_browser_page(p)
        
        file_url = f"file://{os.path.abspath(html_file_path)}"
        page.goto(file_url)
        
        page.wait_for_selector('.plotly-graph-div', timeout=15000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        plotly_div = page.locator('.plotly-graph-div')
        plotly_div.screenshot(
            path=output_path,
            type='png'
        )
        
        browser.close()
        return output_path



def snap_dash(html_file_path, output_path="output/screenshot.png"):
    with sync_playwright() as p:
        browser, page = _get_browser_page(p)
        
        file_url = f"file://{os.path.abspath(html_file_path)}"
        page.goto(file_url)
        
        page.wait_for_selector('#react-entry-point', timeout=15000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        plotly_div = page.locator('#react-entry-point')
        plotly_div.screenshot(
            path=output_path,
            type='png'
        )
        
        browser.close()
        return output_path