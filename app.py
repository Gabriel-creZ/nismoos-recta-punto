from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import math
import matplotlib
matplotlib.use('Agg')  # Usar backend 'Agg' para entornos sin display
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"  # Reemplaza con una clave segura

def calcular_procedimiento(A, B, C, x0, y0):
    pasos = []  # Lista para almacenar cada paso en formato HTML

    # 1. Ecuación inicial de la recta.
    pasos.append(f"<p><strong>1.</strong> Partimos de la ecuación de la recta: <em>{A}x + {B}y + {C} = 0</em>.</p>")
    
    # 2. Cálculo de la pendiente (si B ≠ 0)
    if B != 0:
        m = -A / B
        y_int = -C / B
        pasos.append(f"<p><strong>2.</strong> Como B ≠ 0, calculamos la pendiente:<br>"
                      f"<em>m = -A/B = -({A})/({B}) = {m:.3f}</em>.<br>"
                      f"La ordenada al origen es: <em>y = -C/B = -({C})/({B}) = {y_int:.3f}</em>.</p>")
    else:
        m = None
        y_int = None
        pasos.append("<p><strong>2.</strong> Como B = 0, la recta es vertical y no tiene pendiente ni ordenada al origen.</p>")
    
    # 3. Cálculo del intercepto en X (absisa) si A ≠ 0.
    if A != 0:
        x_int = -C / A
        pasos.append(f"<p><strong>3.</strong> El intercepto en X se halla de <em>Ax + C = 0</em>:<br>"
                      f"x = -C/A = -({C})/({A}) = {x_int:.3f}</p>")
    else:
        x_int = None
        pasos.append("<p><strong>3.</strong> A = 0, no se puede calcular la absisa.</p>")
    
    # 4. Cálculo de la inclinación de la recta (ángulo con el eje X)
    if B != 0 and m is not None:
        angulo = math.degrees(math.atan(m))
        pasos.append(f"<p><strong>4.</strong> La inclinación se obtiene con: <em>θ = arctan(m)</em>:<br>"
                      f"θ = arctan({m:.3f}) = {angulo:.2f}°</p>")
    else:
        angulo = 90
        pasos.append("<p><strong>4.</strong> La recta es vertical, por lo que su inclinación es 90°.</p>")
    
    # 5. Cálculo de la distancia del punto (x0, y0) a la recta.
    numerador = abs(A * x0 + B * y0 + C)
    denominador = math.sqrt(A ** 2 + B ** 2) if (A != 0 or B != 0) else 1
    distancia = numerador / denominador
    pasos.append(f"<p><strong>5.</strong> La distancia del punto <em>({x0},{y0})</em> a la recta se calcula mediante:<br>"
                  f"d = |A·x₀ + B·y₀ + C| / √(A² + B²)<br>"
                  f"= |({A})·({x0}) + ({B})·({y0}) + ({C})| / √(({A})² + ({B})²) = {distancia:.3f}</p>")
    
    # 6. Cálculo de la distancia del punto al origen.
    dist_origen = math.sqrt(x0 ** 2 + y0 ** 2)
    pasos.append(f"<p><strong>6.</strong> La distancia del punto al origen es:<br>"
                  f"√(x₀² + y₀²) = √(({x0})² + ({y0})²) = {dist_origen:.3f}</p>")
    
    procedimiento_html = "".join(pasos)
    return {
        'm': m,
        'y_int': y_int,
        'x_int': x_int,
        'angulo': angulo,
        'distancia': distancia,
        'dist_origen': dist_origen,
        'procedimiento': procedimiento_html
    }

def generar_grafica(A, B, C, x0, y0):
    fig, ax = plt.subplots(figsize=(6, 6))
    rango = (-10, 10)
    ax.set_xlim(rango)
    ax.set_ylim(rango)
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    ax.set_title("Gráfica: Recta y Punto")

    # Graficar la recta
    if B != 0:
        x_vals = [rango[0], rango[1]]
        y_vals = [(-A * x - C) / B for x in x_vals]
        ax.plot(x_vals, y_vals, label="Recta", color="blue")
    else:
        x_val = -C / A
        ax.plot([x_val, x_val], [rango[0], rango[1]], label="Recta Vertical", color="blue")

    # Graficar el punto
    ax.plot(x0, y0, "ro", label="Punto")
    
    # Graficar línea perpendicular (distancia mínima)
    if B != 0:
        m = -A / B
        if m != 0:
            m_perp = -1 / m
            x_inter = (y0 + m_perp * x0 + C / B) / (m - m_perp)
            y_inter = m * x_inter - C / B
        else:
            x_inter = x0
            y_inter = -C / B
    else:
        x_inter = -C / A
        y_inter = y0
    ax.plot([x0, x_inter], [y0, y_inter], label="Distancia (Perpendicular)", color="green", linestyle="--")
    
    ax.legend()
    ax.grid(True)

    # Convertir la gráfica a imagen codificada en Base64
    img = BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    plt.close(fig)
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    return graph_url

# Ruta principal: formulario y cálculo
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            A = float(request.form["A"])
            B = float(request.form["B"])
            C = float(request.form["C"])
            x0 = float(request.form["x0"])
            y0 = float(request.form["y0"])
        except Exception as e:
            flash("Error en la entrada de datos. Verifica que todos los campos tengan valores numéricos válidos.", "error")
            return render_template("index.html", error="Error en la entrada de datos.", resultado=None)
        
        resultado = calcular_procedimiento(A, B, C, x0, y0)
        resultado["graph_url"] = generar_grafica(A, B, C, x0, y0)
        return render_template("resultado.html", resultado=resultado)
    return render_template("index.html", resultado=None)

# Rutas dummy para login, reporte y donar
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Validación dummy: Usuario = "admin", Contraseña = "admin"
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin":
            session["logged_in"] = True
            flash("Has iniciado sesión correctamente.", "success")
            return redirect(url_for("index"))
        else:
            flash("Credenciales inválidas.", "error")
            return render_template("login.html")
    return render_template("login.html")

@app.route("/reporte", methods=["GET", "POST"])
def reporte():
    if request.method == "POST":
        # Aquí se procesa el reporte enviado por el usuario.
        flash("Reporte enviado. ¡Gracias por tu ayuda!", "success")
        return redirect(url_for("index"))
    return render_template("reporte.html")

@app.route("/donar")
def donar():
    # Página dummy de donaciones.
    return render_template("donar.html")

# Ruta dummy para calcular distancia (en caso de usar AJAX en otras funcionalidades)
@app.route("/calcular_distancia", methods=["POST"])
def calcular_distancia():
    data = request.form
    try:
        xA = float(data["xA"])
        yA = float(data["yA"])
        xB = float(data["xB"])
        yB = float(data["yB"])
        dAB = math.sqrt((xB - xA) ** 2 + (yB - yA) ** 2)
        response = {
            "status": "ok",
            "tipo": "puntos",
            "dAB": round(dAB, 3),
            "procedure": f"Cálculo: √(({xB} - {xA})² + ({yB} - {yA})²) = {round(dAB,3)}"
        }
    except Exception as e:
        response = {
            "status": "error",
            "message": "Error al calcular la distancia."
        }
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)