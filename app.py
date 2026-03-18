from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import numpy as np
import io
import zipfile

app = Flask(__name__)

@app.route('/plot', methods=['POST'])
def plot():
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

            # Swap axes if needed
            xplot, yplot = yplot, xplot

            fig, ax = plt.subplots(figsize=(6,6))

            # Draw circles
            radii = [0.01, 0.02, 0.03]
            for r in radii:
                theta = np.linspace(0, 2*np.pi, 300)
                ax.plot(r*np.cos(theta), r*np.sin(theta), color='black', lw=1)
                ax.text(r + 0.001, -0.005, f"{r:.2f}°", va='center', fontsize=10)

            # Draw crosshairs
            ax.plot([-0.03, 0.03], [0, 0], color='black', lw=1, zorder=0)
            ax.plot([0, 0], [-0.03, 0.03], color='black', lw=1, zorder=0)

            # Scatter
            sc = ax.scatter(xplot, yplot, c=dates, s=50, cmap='jet', edgecolors='none')
            plt.colorbar(sc, ax=ax, pad=0.18, label='Date')

            # Formatting
            ax.set_xlim(-0.03, 0.03)
            ax.set_ylim(-0.03, 0.03)
            ax.set_aspect('equal')

            # Remove box
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

            # Labels
            ax.text(0, -0.040, "Rotation (°)", ha='center', fontsize=12, fontweight='bold')
            ax.text(0, 0.032, "North", ha='center', va='bottom', fontsize=12, fontweight='bold')
            ax.text(0, -0.032, "South", ha='center', va='top', fontsize=12, fontweight='bold')
            ax.text(0.032, 0, "East", ha='left', va='center', fontsize=12, fontweight='bold')
            ax.text(-0.032, 0, "West", ha='right', va='center', fontsize=12, fontweight='bold')

            plt.tight_layout()
            plt.subplots_adjust(right=0.85, bottom=0.15)
            
            # Save image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, transparent=True)
            plt.close(fig)
            buf.seek(0)

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
