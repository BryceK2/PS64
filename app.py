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

            # Bullseye circles and labels
            radii = [0.01, 0.02, 0.03]
            for r in radii:
                theta = np.linspace(0, 2*np.pi, 300)
                ax.plot(r*np.cos(theta), r*np.sin(theta), color='black', lw=1)
                # Label circles on the right
                ax.text(r + 0.001, 0, f"{r:.2f}", verticalalignment='center', fontsize=10, fontweight='bold')

            # Scatter tilt data
            sc = ax.scatter(xplot, yplot, c=dates, s=50, cmap='jet', edgecolors='none')
            plt.colorbar(sc, ax=ax, label='Date')

            # Axis limits
            ax.set_xlim(-0.03, 0.03)
            ax.set_ylim(-0.03, 0.03)
            ax.set_aspect('equal')

            # Remove square box and ticks
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

            # ROTATION label
            ax.text(0, -0.035, "ROTATION (deg)", fontsize=12, fontweight='bold', ha='center')

            # Cardinal points
            ax.text(0, 0.032, "N", ha='center', va='bottom', fontsize=12, fontweight='bold')
            ax.text(0, -0.032, "S", ha='center', va='top', fontsize=12, fontweight='bold')
            ax.text(0.032, 0, "E", ha='left', va='center', fontsize=12, fontweight='bold')
            ax.text(-0.032, 0, "W", ha='right', va='center', fontsize=12, fontweight='bold')

            plt.tight_layout()

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, transparent=True)  # transparent background removes square box
            plt.close(fig)
            buf.seek(0)

            # Add PNG to zip
            zf.writestr(f"{sensor_id}.png", buf.read())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='tilt_plots.zip'
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
