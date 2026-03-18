from flask import Flask, request, send_file, jsonify
import matplotlib.pyplot as plt
import numpy as np
import io

app = Flask(__name__)

@app.route('/plot', methods=['POST'])
def plot():
    """
    Expects JSON payload:
    {
        "x": [...],       # X tilt data
        "y": [...],       # Y tilt data
        "dates": [...]    # Excel serial dates or numeric timestamps
    }
    """
    data = request.get_json()
    
    try:
        xplot = np.array(data['x'])
        yplot = np.array(data['y'])
        dates = np.array(data['dates'], dtype=float)

        # Swap X/Y if needed (match your MATLAB orientation)
        xplot, yplot = yplot, xplot

        fig, ax = plt.subplots(figsize=(6,6))

        # Draw bullseye rings
        for r in [0.01, 0.02, 0.03]:
            theta = np.linspace(0, 2*np.pi, 200)
            ax.plot(r*np.cos(theta), r*np.sin(theta), color='black')

        # Scatter plot colored by date
        sc = ax.scatter(xplot, yplot, c=dates, s=50, cmap='jet', edgecolors='none')
        cb = plt.colorbar(sc)
        cb.set_label('Date')

        # Axis limits and formatting
        ax.set_xlim(-0.03, 0.03)
        ax.set_ylim(-0.03, 0.03)
        ax.set_aspect('equal')
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.set_xticks([0.01, 0.02, 0.03])
        ax.set_yticks([0.01, 0.02, 0.03])
        ax.grid(True)

        # Save plot to in-memory buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close(fig)

        return send_file(buf, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
