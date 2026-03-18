from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import numpy as np
import io
import zipfile

app = Flask(__name__)

@app.route('/plot', methods=['POST'])
def plot():
    """
    Expects JSON payload like:
    {
        "sensors": [
            {
                "id": "150845",
                "x": [...],
                "y": [...],
                "dates": [...]
            },
            {
                "id": "150940",
                "x": [...],
                "y": [...],
                "dates": [...]
            }
        ]
    }
    Returns a zip of PNGs (one per sensor)
    """
    data = request.get_json()
    sensors = data.get("sensors", [])

    if not sensors:
        return jsonify({"error": "No sensor data provided"}), 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for sensor in sensors:
            sensor_id = sensor.get("id", "unknown")
            xplot = np.array(sensor["x"])
            yplot = np.array(sensor["y"])
            dates = np.array(sensor["dates"], dtype=float)
            xplot, yplot = yplot, xplot  # swap if needed

            fig, ax = plt.subplots(figsize=(6,6))

            # Bullseye rings
            for r in [0.01, 0.02, 0.03]:
                theta = np.linspace(0, 2*np.pi, 200)
                ax.plot(r*np.cos(theta), r*np.sin(theta), color='black')

            # Scatter
            sc = ax.scatter(xplot, yplot, c=dates, s=50, cmap='jet', edgecolors='none')
            plt.colorbar(sc, ax=ax, label='Date')

            ax.set_xlim(-0.03, 0.03)
            ax.set_ylim(-0.03, 0.03)
            ax.set_aspect('equal')
            ax.set_xticks([0.01, 0.02, 0.03])
            ax.set_yticks([0.01, 0.02, 0.03])
            ax.tick_params(axis='both', which='major', labelsize=12)
            plt.tight_layout()

            # Save figure to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150)
            plt.close(fig)
            buf.seek(0)
            
            # Add PNG to zip
            zf.writestr(f"{sensor_id}.png", buf.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, attachment_filename='tilt_plots.zip')

if __name__ == "__main__":
    app.run(debug=True)
