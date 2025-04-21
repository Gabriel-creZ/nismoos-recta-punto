from flask import Flask, render_template, request, jsonify, session, flash
import math, numpy as np, io, base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'j350z271123r'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1h

# SMTP config
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'castilloreyesgabriel4@gmail.com'
SMTP_PASSWORD = 'wkiqrqkcvhoirdyr'


# ——— Funciones de cálculo y graficado (idénticas a las tuyas) ———

def resolverSistema(a1, b1, c1, a2, b2, c2):
    det = a1*b2 - a2*b1
    resultado = {"det": det, "tipo": None, "punto": None}
    if abs(det) < 1e-14:
        # paralelas/coincidentes
        proporcion = None
        if abs(a2)>1e-14: proporcion = a1/a2
        elif abs(b2)>1e-14: proporcion = b1/b2
        elif abs(c2)>1e-14: proporcion = c1/c2
        if proporcion is not None:
            check_b = abs(b1 - proporcion*b2)<1e-9
            check_c = abs(c1 - proporcion*c2)<1e-9
            resultado["tipo"] = "coincidentes" if (check_b and check_c) else "paralelas"
        else:
            resultado["tipo"] = "indefinido"
    else:
        dx = (-c1)*b2 - (-c2)*b1
        dy = a1*(-c2) - a2*(-c1)
        resultado["tipo"] = "interseccion"
        resultado["punto"] = (dx/det, dy/det)
    return resultado

def calcularDatosRecta(a, b, c):
    datos = {}
    datos["pendiente"] = None if abs(b)<1e-14 else -a/b
    datos["interseccionX"] = None if abs(a)<1e-14 else -c/a
    datos["interseccionY"] = None if abs(b)<1e-14 else -c/b
    if datos["pendiente"] is None:
        datos["anguloConEjeX"] = 90.0
    else:
        datos["anguloConEjeX"] = round(math.degrees(math.atan(abs(datos["pendiente"]))), 2)
    datos["distanciaAlOrigen"] = round(abs(c)/math.sqrt(a*a + b*b), 2)
    return datos

def calcularDistancia(p1, p2):
    return round(math.hypot(p2[0]-p1[0], p2[1]-p1[1]), 2)

def calcularAnguloEntreRectas(m1, m2):
    ang1 = 90.0 if m1 is None else math.degrees(math.atan(m1))
    ang2 = 90.0 if m2 is None else math.degrees(math.atan(m2))
    ang = abs(ang1 - ang2)
    return round((180-ang) if ang>90 else ang, 2)

def graficarUnaRecta(a, b, c):
    fig = plt.figure(figsize=(7,7))
    xs = np.linspace(-10,10,400)
    if abs(b)>1e-14:
        ys = (-a*xs - c)/b
        plt.plot(xs, ys, color='darkorange', label=f'{a}x+{b}y+{c}=0')
    else:
        x0 = -c/a
        plt.axvline(x0, color='darkorange', label=f'x={x0:.2f}')
    plt.axhline(0,color='black',linewidth=0.5)
    plt.axvline(0,color='black',linewidth=0.5)
    plt.legend(); plt.grid(True); plt.axis('equal')
    buf = io.BytesIO()
    plt.savefig(buf, format='png'); buf.seek(0); plt.close()
    return buf

def graficarUnaRectaInteractivo(a,b,c):
    xs = np.linspace(-10,10,400)
    fig = go.Figure()
    if abs(b)>1e-14:
        ys = (-a*xs - c)/b
        fig.add_trace(go.Scatter(x=xs,y=ys,mode='lines',name=f'{a}x+{b}y+{c}=0'))
    else:
        x0 = -c/a
        fig.add_trace(go.Scatter(x=[x0,x0],y=[-10,10],mode='lines',name=f'x={x0:.2f}'))
    fig.update_layout(template='plotly_white',title='Gráfica Interactiva',xaxis_title='X',yaxis_title='Y')
    return fig.to_html(full_html=False)

# Para dos y tres rectas: conserva tus funciones graficarRectas/graficarRectasInteractivo/graficarTres...


# ——— Rutas SPA ———

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/solve", methods=["POST"])
def api_solve():
    modo = request.form.get("modo","dos")
    html = ""
    if modo=="una":
        a1,b1,c1 = map(float,(request.form["a1"],request.form["b1"],request.form["c1"]))
        datos1 = calcularDatosRecta(a1,b1,c1)
        buf = graficarUnaRecta(a1,b1,c1)
        grafico_est = base64.b64encode(buf.getvalue()).decode()
        grafico_int = graficarUnaRectaInteractivo(a1,b1,c1)
        html = render_template("partials/solve.html",
                               modo="una", datos1=datos1,
                               grafico_estatico=grafico_est,
                               grafico_interactivo=grafico_int)
    elif modo=="dos":
        a1,b1,c1,a2,b2,c2 = [float(request.form[k]) for k in ("a1","b1","c1","a2","b2","c2")]
        resultado = resolverSistema(a1,b1,c1,a2,b2,c2)
        datos1 = calcularDatosRecta(a1,b1,c1)
        datos2 = calcularDatosRecta(a2,b2,c2)
        # comparaciones
        p1 = datos1["pendiente"] or float('inf')
        p2 = datos2["pendiente"] or float('inf')
        if abs(p1)>abs(p2): comp_p = f"🔥 La recta 1 tiene mayor pendiente: {datos1['pendiente']}"
        elif abs(p2)>abs(p1): comp_p = f"🔥 La recta 2 tiene mayor pendiente: {datos2['pendiente']}"
        else: comp_p = "🔥 Ambas tienen la misma pendiente."
        if datos1["anguloConEjeX"]>datos2["anguloConEjeX"]:
            comp_i = f"🌟 La recta 1 más inclinada: {datos1['anguloConEjeX']}°"
        elif datos2["anguloConEjeX"]>datos1["anguloConEjeX"]:
            comp_i = f"🌟 La recta 2 más inclinada: {datos2['anguloConEjeX']}°"
        else:
            comp_i = "🌟 Ídem en inclinación."
        ang_entre = calcularAnguloEntreRectas(datos1["pendiente"], datos2["pendiente"])
        dist_int = None
        if resultado["tipo"]=="interseccion":
            dist_int = calcularDistancia((0,0), resultado["punto"])
        # gráficas
        from your_module import graficarRectas, graficarRectasInteractivo  # importa tus funciones
        buf = graficarRectas(a1,b1,c1,a2,b2,c2, resultado)
        grafico_est = base64.b64encode(buf.getvalue()).decode()
        grafico_int = graficarRectasInteractivo(a1,b1,c1,a2,b2,c2, resultado)
        html = render_template("partials/solve.html",
                               modo="dos", resultado=resultado,
                               datos1=datos1, datos2=datos2,
                               comp_pendiente=comp_p, comp_inclinacion=comp_i,
                               angulo_entre=ang_entre,
                               distancia_interseccion=dist_int,
                               grafico_estatico=grafico_est,
                               grafico_interactivo=grafico_int)
    else:  # modo tres
        a1,b1,c1,a2,b2,c2,a3,b3,c3 = [float(request.form[k]) for k in ("a1","b1","c1","a2","b2","c2","a3","b3","c3")]
        datos1 = calcularDatosRecta(a1,b1,c1)
        datos2 = calcularDatosRecta(a2,b2,c2)
        datos3 = calcularDatosRecta(a3,b3,c3)
        i12 = resolverSistema(a1,b1,c1,a2,b2,c2)
        i13 = resolverSistema(a1,b1,c1,a3,b3,c3)
        i23 = resolverSistema(a2,b2,c2,a3,b3,c3)
        inters = {}
        if i12["tipo"]=="interseccion": inters["12"]=i12["punto"]
        if i13["tipo"]=="interseccion": inters["13"]=i13["punto"]
        if i23["tipo"]=="interseccion": inters["23"]=i23["punto"]
        from your_module import graficarTresRectas, graficarTresRectasInteractivo
        buf = graficarTresRectas(a1,b1,c1,a2,b2,c2,a3,b3,c3,inters)
        grafico_est = base64.b64encode(buf.getvalue()).decode()
        grafico_int = graficarTresRectasInteractivo(a1,b1,c1,a2,b2,c2,a3,b3,c3,inters)
        html = render_template("partials/solve.html",
                               modo="tres",
                               datos1=datos1, datos2=datos2, datos3=datos3,
                               intersecciones=inters,
                               grafico_estatico=grafico_est,
                               grafico_interactivo=grafico_int)
    return jsonify(html=html)


@app.route("/api/recta-punto", methods=["POST"])
def api_recta_punto():
    x0 = float(request.form["x0"])
    y0 = float(request.form["y0"])
    m  = float(request.form["m"])
    # y - y0 = m (x - x0) → m x - y + (y0 - m x0) = 0
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
        return jsonify(success=True, message="Reporte enviado. ¡Gracias!")
    except Exception as e:
        return jsonify(success=False, message=f"Error: {e}")

if __name__ == "__main__":
    app.run(debug=True)