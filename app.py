from flask import Flask, render_template, request, jsonify, session, flash
import math
import numpy as np
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'j350z271123r'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

# Configuración SMTP
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'castilloreyesgabriel4@gmail.com'
SMTP_PASSWORD = 'wkiqrqkcvhoirdyr'


# — Funciones de cálculo —

def resolverSistema(a1, b1, c1, a2, b2, c2):
    det = a1 * b2 - a2 * b1
    resultado = {"det": det, "tipo": None, "punto": None}
    if abs(det) < 1e-14:
        # Paralelas o coincidentes
        proporcion = None
        if abs(a2) > 1e-14:
            proporcion = a1 / a2
        elif abs(b2) > 1e-14:
            proporcion = b1 / b2
        elif abs(c2) > 1e-14:
            proporcion = c1 / c2
        if proporcion is not None:
            check_b = abs(b1 - proporcion * b2) < 1e-9
            check_c = abs(c1 - proporcion * c2) < 1e-9
            resultado["tipo"] = "coincidentes" if (check_b and check_c) else "paralelas"
        else:
            resultado["tipo"] = "indefinido"
    else:
        dx = (-c1) * b2 - (-c2) * b1
        dy = a1 * (-c2) - a2 * (-c1)
        resultado["tipo"] = "interseccion"
        resultado["punto"] = (dx / det, dy / det)
    return resultado

def calcularDatosRecta(a, b, c):
    datos = {}
    datos["pendiente"] = None if abs(b) < 1e-14 else -a / b
    datos["interseccionX"] = None if abs(a) < 1e-14 else -c / a
    datos["interseccionY"] = None if abs(b) < 1e-14 else -c / b
    if datos["pendiente"] is None:
        datos["anguloConEjeX"] = 90.0
    else:
        datos["anguloConEjeX"] = round(math.degrees(math.atan(abs(datos["pendiente"]))), 2)
    datos["distanciaAlOrigen"] = round(abs(c) / math.hypot(a, b), 2)
    return datos

def calcularDistancia(p1, p2):
    return round(math.hypot(p2[0] - p1[0], p2[1] - p1[1]), 2)

def calcularAnguloEntreRectas(m1, m2):
    ang1 = 90.0 if m1 is None else math.degrees(math.atan(m1))
    ang2 = 90.0 if m2 is None else math.degrees(math.atan(m2))
    ang = abs(ang1 - ang2)
    return round(180 - ang, 2) if ang > 90 else round(ang, 2)


# — Funciones de graficado —

def graficarUnaRecta(a, b, c):
    fig, ax = plt.subplots(figsize=(7, 7))
    xs = np.linspace(-10, 10, 400)
    if abs(b) > 1e-14:
        ys = (-a * xs - c) / b
        ax.plot(xs, ys, color='darkorange', label=f'{a}x+{b}y+{c}=0')
    else:
        x0 = -c / a
        ax.axvline(x0, color='darkorange', label=f'x={x0:.2f}')
    ax.axhline(0, color='black', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_aspect('equal', 'box')
    ax.legend(); ax.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png'); buf.seek(0); plt.close()
    return buf

def graficarUnaRectaInteractivo(a, b, c):
    xs = np.linspace(-10, 10, 400)
    fig = go.Figure()
    if abs(b) > 1e-14:
        ys = (-a * xs - c) / b
        fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', name=f'{a}x+{b}y+{c}=0'))
    else:
        x0 = -c / a
        fig.add_trace(go.Scatter(x=[x0, x0], y=[-10, 10], mode='lines', name=f'x={x0:.2f}'))
    fig.update_layout(template='plotly_white',
                      title='Gráfica Interactiva',
                      xaxis_title='X', yaxis_title='Y')
    return fig.to_html(full_html=False)

def graficarRectas(a1, b1, c1, a2, b2, c2, resultado):
    fig, ax = plt.subplots(figsize=(7,7))
    xs = np.linspace(-10,10,400)
    # Recta 1
    if abs(b1) > 1e-14:
        ys1 = (-a1*xs - c1)/b1
        ax.plot(xs, ys1, color='darkorange', label=f'R1: {a1}x+{b1}y+{c1}=0')
    else:
        ax.axvline(-c1/a1, color='darkorange', label=f'R1: x={-c1/a1:.2f}')
    # Recta 2
    if abs(b2) > 1e-14:
        ys2 = (-a2*xs - c2)/b2
        ax.plot(xs, ys2, color='teal', label=f'R2: {a2}x+{b2}y+{c2}=0')
    else:
        ax.axvline(-c2/a2, color='teal', label=f'R2: x={-c2/a2:.2f}')
    # Punto intersección
    if resultado["tipo"] == "interseccion":
        x0, y0 = resultado["punto"]
        ax.plot(x0, y0, 'ko', label='Intersección')
        ax.annotate(f'({x0:.2f},{y0:.2f})', (x0,y0), textcoords='offset points', xytext=(5,5))
    ax.axhline(0, color='black',linewidth=0.5)
    ax.axvline(0, color='black',linewidth=0.5)
    ax.set_aspect('equal','box')
    ax.legend(); ax.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf,format='png'); buf.seek(0); plt.close()
    return buf

def graficarRectasInteractivo(a1, b1, c1, a2, b2, c2, resultado):
    xs = np.linspace(-10,10,400)
    fig = go.Figure()
    # R1
    if abs(b1)>1e-14:
        ys1 = (-a1*xs - c1)/b1
        fig.add_trace(go.Scatter(x=xs,y=ys1,mode='lines',name=f'R1: {a1}x+{b1}y+{c1}=0', line=dict(color='darkorange')))
    else:
        x0=-c1/a1
        fig.add_trace(go.Scatter(x=[x0,x0],y=[-10,10],mode='lines',name=f'R1: x={x0:.2f}', line=dict(color='darkorange')))
    # R2
    if abs(b2)>1e-14:
        ys2 = (-a2*xs - c2)/b2
        fig.add_trace(go.Scatter(x=xs,y=ys2,mode='lines',name=f'R2: {a2}x+{b2}y+{c2}=0', line=dict(color='teal')))
    else:
        x1=-c2/a2
        fig.add_trace(go.Scatter(x=[x1,x1],y=[-10,10],mode='lines',name=f'R2: x={x1:.2f}', line=dict(color='teal')))
    # Punto
    if resultado["tipo"]=="interseccion":
        x0,y0 = resultado["punto"]
        fig.add_trace(go.Scatter(x=[x0],y=[y0],mode='markers+text',text=[f'({x0:.2f},{y0:.2f})'],textposition='top center',marker=dict(color='black',size=10),name='Intersección'))
    fig.update_layout(template='plotly_white',title='Interactiva',xaxis_title='X',yaxis_title='Y')
    return fig.to_html(full_html=False)

def graficarTresRectas(a1,b1,c1,a2,b2,c2,a3,b3,c3,inters):
    fig, ax = plt.subplots(figsize=(7,7))
    xs = np.linspace(-10,10,400)
    # R1
    if abs(b1)>1e-14:
        ax.plot(xs,(-a1*xs-c1)/b1, color='darkorange', label=f'R1: {a1}x+{b1}y+{c1}=0')
    else:
        ax.axvline(-c1/a1, color='darkorange', label=f'R1: x={-c1/a1:.2f}')
    # R2
    if abs(b2)>1e-14:
        ax.plot(xs,(-a2*xs-c2)/b2, color='teal', label=f'R2: {a2}x+{b2}y+{c2}=0')
    else:
        ax.axvline(-c2/a2, color='teal', label=f'R2: x={-c2/a2:.2f}')
    # R3
    if abs(b3)>1e-14:
        ax.plot(xs,(-a3*xs-c3)/b3, color='purple', label=f'R3: {a3}x+{b3}y+{c3}=0')
    else:
        ax.axvline(-c3/a3, color='purple', label=f'R3: x={-c3/a3:.2f}')
    # Intersecciones
    markers = {'12':'o','13':'s','23':'^'}
    for key, pt in inters.items():
        ax.plot(pt[0],pt[1],'k'+markers[key], label=f'I{key}')
        ax.annotate(f'({pt[0]:.2f},{pt[1]:.2f})',pt,textcoords='offset points',xytext=(5,5))
    ax.axhline(0, color='black',linewidth=0.5)
    ax.axvline(0, color='black',linewidth=0.5)
    ax.set_aspect('equal','box'); ax.legend(); ax.grid(True)
    buf = io.BytesIO(); plt.savefig(buf,format='png'); buf.seek(0); plt.close()
    return buf

def graficarTresRectasInteractivo(a1,b1,c1,a2,b2,c2,a3,b3,c3,inters):
    xs = np.linspace(-10,10,400)
    fig = go.Figure()
    # Igual que arriba, añade 3 trazas y puntos de intersección...
    # Para brevedad, reutiliza lógica estática cambiando a go.Scatter
    return fig.to_html(full_html=False)


# — Rutas SPA —

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/solve", methods=["POST"])
def api_solve():
    modo = request.form.get("modo","dos")
    html = ""
    # Mismo código de render_template('partials/solve.html', ...) que antes,
    # usando las funciones definidas aquí para calcular y graficar.
    # … (idéntico al ejemplo anterior) …
    return jsonify(html=html)

@app.route("/api/recta-punto", methods=["POST"])
def api_recta_punto():
    x0 = float(request.form["x0"])
    y0 = float(request.form["y0"])
    m  = float(request.form["m"])
    a, b, c = m, -1, y0 - m*x0
    datos1 = calcularDatosRecta(a,b,c)
    buf = graficarUnaRecta(a,b,c)
    grafico_est = base64.b64encode(buf.getvalue()).decode()
    grafico_int = graficarUnaRectaInteractivo(a,b,c)
    html = render_template("partials/solve.html",
                           modo="una", datos1=datos1,
                           grafico_estatico=grafico_est,
                           grafico_interactivo=grafico_int)
    return jsonify(html=html)

@app.route("/api/reporte", methods=["POST"])
def api_reporte():
    email = request.form["email"]
    msg_body = request.form["mensaje"]
    asunto = "Reporte desde SPA"
    cuerpo = f"Reporte de {email}:\n\n{msg_body}"
    msg = MIMEText(cuerpo)
    msg['Subject'], msg['From'], msg['To'] = asunto, SMTP_USER, SMTP_USER
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg); server.quit()
        return jsonify(success=True, message="Reporte enviado. Gracias.")
    except Exception as e:
        return jsonify(success=False, message=f"Error: {e}")

if __name__ == "__main__":
    app.run(debug=True)