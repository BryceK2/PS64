from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import numpy as np
import io
import zipfile
from datetime import datetime, timedelta

app = Flask(__name__)

# Convert Excel serial date → datetime
def excel_to_datetime(excel_date):
    return datetime(1899, 12, 30) + timedelta(days=float(excel_date))

# "Nice" step function for axis/ring scaling
def nice_step(value):
    exponent = np.floor(np.log10(value))
    fraction = value / (10**exponent)
    if fraction <= 1:
        nice_fraction = 1
    elif fraction <= 2:
        nice_fraction = 2
    elif fraction <= 5:
        nice_fraction = 5
    else:
        nice_fraction = 10
    return nice_fraction * (10**exponent)

@app.route('/plot', methods=['POST'])
def plot():
    data = request.get_json()
    sensors = data.get("sensors", [])

    if not sensors:
        return jsonify({"error": "No sensor data provided"}), 400

    # -----------------------------
    # Compute global max radius for all sensors
    # -----------------------------
    all_radii = []
    for sensor in sensors:
        x = np.array(sensor["x"])
        y = np.array(sensor["y"])
        all_radii.extend(np.sqrt(x**2 + y**2))
    global_r_max = np.max(all_radii) if all_radii else 0.001

    raw_step = global_r_max / 3
    step = nice_step(raw_step)
    global_radii = [step, 2*step, 3*step]
    limit = global_radii[-1] * 1.2

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for sensor in sensors:
            sensor_id = sensor.get("id", "unknown")
            xplot = np.array(sensor["x"])
            yplot = np.array(sensor["y"])
            dates = np.array(sensor["dates"], dtype=float)

            fig, ax = plt.subplots(figsize=(6,6))
            ax.set_title("Tilt Monitor", fontsize=14, fontweight='bold', pad=34)

            # -----------------------------
            # Draw circles
            # -----------------------------
            def format_radius(r):
                if r < 0.01:
                    return f"{r:.3f}"
                elif r < 1:
                    return f"{r:.2f}"
                else:
                    return f"{r:.1f}"

            for r in global_radii:
                theta = np.linspace(0, 2*np.pi, 300)
                ax.plot(r*np.cos(theta), r*np.sin(theta), color='black', lw=1)
                ax.text(r + 0.02*limit, -0.05*limit, format_radius(r), fontsize=10)

            # -----------------------------
            # Crosshairs
            # -----------------------------
            ax.plot([-limit, limit], [0,0], color='black', lw=1, zorder=0)
            ax.plot([0,0], [-limit, limit], color='black', lw=1, zorder=0)

            # -----------------------------
            # Scatter: timestamps as dots colored by date
            # -----------------------------
            sc = ax.scatter(xplot, yplot, c=dates, s=50, cmap='jet', edgecolors='none', zorder=3)
            sc.set_clim(dates.min(), dates.max())

            # Colorbar
            cbar = plt.colorbar(sc, ax=ax, pad=0.18)
            span_days = dates.max() - dates.min()
            num_ticks = 4 if span_days < 1 else 5 if span_days < 7 else 6
            tick_vals = np.linspace(dates.min(), dates.max(), num_ticks)
            tick_labels = [
                excel_to_datetime(d).strftime("%b %d\n%H:%M") if span_days < 2
                else excel_to_datetime(d).strftime("%b %d %Y")
                for d in tick_vals
            ]
            cbar.set_ticks(tick_vals)
            cbar.set_ticklabels(tick_labels)
            cbar.set_label('Date', fontsize=10, fontweight='bold')

            # -----------------------------
            # Start/End markers
            # -----------------------------
            ax.scatter(xplot[0], yplot[0], color='green', s=80, zorder=4)
            ax.scatter(xplot[-1], yplot[-1], color='red', s=80, zorder=4)

            # -----------------------------
            # Axes formatting & labels
            # -----------------------------
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            ax.set_aspect('equal')

            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

            ax.text(0, -0.044, "Rotation (°)", ha='center', fontsize=12, fontweight='bold')
            ax.text(0, 0.032, "North", ha='center', va='bottom', fontsize=12, fontweight='bold')
            ax.text(0, -0.032, "South", ha='center', va='top', fontsize=12, fontweight='bold')
            ax.text(0.032, 0, "East", ha='left', va='center', fontsize=12, fontweight='bold')
            ax.text(-0.032, 0, "West", ha='right', va='center', fontsize=12, fontweight='bold')

            plt.tight_layout()
            plt.subplots_adjust(right=0.85, bottom=0.15, top=0.90)

            # Save to zip
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
    app.run(debug=True)
