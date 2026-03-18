from flask import Flask, request, send_file
import matplotlib.pyplot as plt
import numpy as np
import io
import pandas as pd

app = Flask(__name__)

@app.route('/plot', methods=['POST'])
def plot():
    """
    Expects JSON payload:
    {
        "dates": [...],       # serial numbers or datetime strings
        "x": [...],
        "y": [...]
    }
    """
    data = request.get_json()
    xplot = np.array(data['x'])
    yplot = np.array(data['y'])
    dates = np.array(data['dates'], dtype=float)  # if numeric, else parse datetime

    # --- Bullseye circles ---
    fig, ax = plt.subplots(figsize=(6,6))
    for r in [0.01, 0.02, 0.03]:
        theta = np.linspace(0, 2*np.pi, 200)
        ax.plot(r*np.cos(theta), r*np.sin(theta), color='black')

    # --- Scatter plot colored by date ---
    scatter = ax.scatter(xplot, yplot, c=dates, s=50, cmap='jet', edgecolors='none')

    # --- Colorbar like MATLAB example ---
    cb = plt.colorbar(scatter)
    # Optional: you can map date serials to ticks/labels
    cb.set_label('Date')
    # Example: adjust ticks if numeric serials
    # cb.set_ticks([dates.min(), dates.mean(), dates.max()])
    # cb.set_ticklabels(['Start', 'Middle', 'End'])

    # --- Axis limits ---
    ax.set_xlim(-0.03, 0.03)
    ax.set_ylim(-0.03, 0.03)
    ax.set_aspect('equal')
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_xticks([0.01, 0.02, 0.03])
    ax.set_yticks([0.01, 0.02, 0.03])
    ax.grid(True)

    # --- Render figure to PNG in-memory ---
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
