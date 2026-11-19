from __future__ import annotations

import math
import random
from fractions import Fraction
from pathlib import Path

SEED = 2026
POR_COMPONENTE = 50
BASICO, INTERMEDIO, AVANZADO = 1, 2, 3
COMP_ESTADISTICA, COMP_GEOMETRIA, COMP_CALCULO = 1, 2, 3

rng = random.Random(SEED)


def fmt(x) -> str:
    if isinstance(x, Fraction):
        if x.denominator == 1:
            return str(x.numerator)
        return f"{x.numerator}/{x.denominator}"
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return str(x)


def opciones(correcta, candidatos, relleno=None):
    correcta = fmt(correcta) if not isinstance(correcta, str) else correcta
    vistos = {correcta}
    distractores = []
    for c in candidatos:
        s = fmt(c) if not isinstance(c, str) else c
        if s not in vistos:
            vistos.add(s)
            distractores.append(s)
        if len(distractores) == 3:
            break
    if len(distractores) < 3 and relleno is None:
        return None, None
    k = 1
    while len(distractores) < 3:
        base = relleno
        for s in (fmt(base + k), fmt(base - k)):
            if s not in vistos and len(distractores) < 3:
                vistos.add(s)
                distractores.append(s)
        k += 1
    todas = [correcta] + distractores
    rng.shuffle(todas)
    return todas, "ABCD"[todas.index(correcta)]


def lista(nums):
    return ", ".join(str(n) for n in nums)


def e_media():
    n = 5
    m = rng.randint(4, 20)
    datos = [m + d for d in rng.sample(range(-6, 7), n - 1)]
    datos.append(m * n - sum(datos))
    if min(datos) <= 0:
        return None
    rng.shuffle(datos)
    med = sorted(datos)[2]
    return (f"Las calificaciones (sobre 30) de 5 estudiantes fueron: {lista(datos)}. ¿Cuál es la media aritmética?",
            m, [med, m + 1, sum(datos) / 4, m - 2], BASICO, m)


def e_mediana():
    datos = sorted(rng.sample(range(2, 40), 6))
    med = (datos[2] + datos[3]) / 2
    media = round(sum(datos) / 6, 2)
    orden = list(datos)
    rng.shuffle(datos)
    return (f"Halle la mediana del conjunto de datos: {lista(datos)}.",
            float(med), [float(datos[2]), float(orden[2]), media, float(orden[3]), float(datos[3])],
            INTERMEDIO, None)


def e_moda():
    moda = rng.randint(1, 15)
    otros = rng.sample([x for x in range(1, 16) if x != moda], 5)
    datos = otros + [moda, moda, moda]
    datos += [otros[0]]
    rng.shuffle(datos)
    return (f"En una encuesta sobre el número de libros leídos al año se obtuvo: {lista(datos)}. ¿Cuál es la moda?",
            moda, [otros[0], max(datos), sorted(datos)[len(datos) // 2]], BASICO, moda)


def e_rango():
    datos = rng.sample(range(5, 95), 7)
    r = max(datos) - min(datos)
    return (f"Los puntajes (sobre 100) de 7 estudiantes en una prueba fueron: {lista(datos)}. ¿Cuál es el rango de los datos?",
            r, [max(datos), max(datos) + min(datos), r - 1], BASICO, r)


def e_dado():
    k = rng.randint(1, 5)
    tipo = rng.choice(["mayor", "menor"])
    fav = 6 - k if tipo == "mayor" else k - 1
    if fav == 0:
        return None
    p = Fraction(fav, 6)
    return (f"Se lanza un dado justo de seis caras. ¿Cuál es la probabilidad de obtener un número {tipo} que {k}?",
            p, [Fraction(fav + 1, 6), Fraction(1, 6), Fraction(fav, 5), 1 - p], BASICO, None)


def e_urna():
    r, a, v = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 8)
    t = r + a + v
    p = Fraction(a + v, t)
    return (f"Una urna contiene {r} balotas rojas, {a} azules y {v} verdes. Si se extrae una al azar, ¿cuál es la probabilidad de que NO sea roja?",
            p, [Fraction(r, t), Fraction(a, t), Fraction(v, t), Fraction(a + v, t + 1)], INTERMEDIO, None)


def e_combinaciones():
    n, k = rng.randint(5, 12), rng.randint(2, 4)
    c = math.comb(n, k)
    return (f"¿De cuántas formas se puede elegir un comité de {k} personas a partir de un grupo de {n} estudiantes (el orden no importa)?",
            c, [math.perm(n, k), n * k, math.comb(n, k - 1)], INTERMEDIO, c)


def e_permutaciones():
    n, k = rng.randint(6, 15), 3
    p = math.perm(n, k)
    return (f"En una carrera participan {n} atletas. ¿De cuántas maneras distintas se pueden asignar el primero, segundo y tercer puesto?",
            p, [math.comb(n, k), n ** k, n * k], INTERMEDIO, p)


def e_varianza():
    desv = rng.choice([[-2, -1, 0, 1, 2], [-3, -1, 1, 3], [-4, 0, 0, 4], [-2, -2, 2, 2], [-6, -2, 2, 6], [-3, 0, 0, 0, 3], [-5, -1, 1, 5]])
    m = rng.randint(5, 30)
    datos = [m + d for d in desv]
    var = Fraction(sum(d * d for d in desv), len(desv))
    var_m = Fraction(sum(d * d for d in desv), len(desv) - 1)
    rng.shuffle(datos)
    return (f"Calcule la varianza POBLACIONAL de los datos: {lista(datos)}.",
            float(var), [float(var_m), math.sqrt(var), float(m), float(var + 1)], AVANZADO, None)


def e_desviacion():
    d = rng.randint(1, 6)
    m = rng.randint(10, 40)
    datos = [m - d, m - d, m + d, m + d]
    rng.shuffle(datos)
    return (f"¿Cuál es la desviación estándar poblacional de los datos {lista(datos)}?",
            d, [d * d, 2 * d, m, 0], AVANZADO, d)


def e_dos_dados():
    s = rng.randint(3, 11)
    fav = sum(1 for a in range(1, 7) for b in range(1, 7) if a + b == s)
    p = Fraction(fav, 36)
    return (f"Se lanzan dos dados justos. ¿Cuál es la probabilidad de que la suma de los resultados sea {s}?",
            p, [Fraction(1, 11), Fraction(fav, 12), Fraction(fav + 1, 36), Fraction(1, 6) if p != Fraction(1, 6) else Fraction(1, 9)],
            AVANZADO, None)


def e_ponderada():
    pesos = rng.choice([(30, 30, 40), (20, 30, 50), (25, 25, 50), (40, 30, 30)])
    notas = [round(rng.uniform(2.0, 5.0), 1) for _ in range(3)]
    def_ = sum(n * p for n, p in zip(notas, pesos)) / 100
    simple = sum(notas) / 3
    return (f"Un estudiante obtuvo notas de {fmt(notas[0])}; {fmt(notas[1])} y {fmt(notas[2])} en tres cortes que valen "
            f"{pesos[0]}%, {pesos[1]}% y {pesos[2]}% respectivamente. ¿Cuál es su nota definitiva?",
            round(def_, 2), [round(simple, 2), round(def_ + 0.3, 2), round(max(notas), 2)], INTERMEDIO, None)


def e_frecuencia():
    n = rng.choice([40, 50, 80, 120, 200, 250])
    f = rng.randint(1, n // 2)
    pct = Fraction(f * 100, n)
    if pct.denominator != 1:
        return None
    return (f"En una encuesta a {n} estudiantes, {f} prefieren estudiar en la mañana. ¿Qué porcentaje representa esta frecuencia relativa?",
            f"{fmt(pct)}%", [f"{fmt(f / n)}%", f"{f}%", f"{fmt(100 - pct)}%", f"{fmt(pct * 2)}%"], BASICO, None)


def e_cuartil():
    datos = sorted(rng.sample(range(1, 60), 7))
    q1 = datos[1]
    rng.shuffle(datos)
    s = sorted(datos)
    return (f"Ordene los datos {lista(datos)} y halle el primer cuartil Q1 (mediana de la mitad inferior, sin incluir la mediana).",
            q1, [s[0], s[3], s[2], s[5]], AVANZADO, q1)


ESTADISTICA = [e_media, e_mediana, e_moda, e_rango, e_dado, e_urna, e_combinaciones, e_permutaciones,
               e_varianza, e_desviacion, e_dos_dados, e_ponderada, e_frecuencia, e_cuartil]

TERNAS = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (6, 8, 10), (9, 12, 15), (20, 21, 29), (12, 16, 20), (9, 40, 41)]


def pi(x):
    return f"{fmt(x)}π"


def g_area_rect():
    b, h = rng.randint(3, 25), rng.randint(2, 20)
    return (f"Un terreno rectangular mide {b} m de largo y {h} m de ancho. ¿Cuál es su área?",
            f"{b*h} m²", [f"{2*(b+h)} m²", f"{b+h} m²", f"{b*h//2} m²"], BASICO, None)


def g_perim_rect():
    b, h = rng.randint(3, 30), rng.randint(2, 25)
    return (f"¿Cuál es el perímetro de un rectángulo de {b} cm de base y {h} cm de altura?",
            f"{2*(b+h)} cm", [f"{b*h} cm", f"{b+h} cm", f"{2*b+h} cm"], BASICO, None)


def g_area_tri():
    b, h = rng.randint(4, 30), rng.randint(3, 20)
    a = Fraction(b * h, 2)
    return (f"Un triángulo tiene base {b} cm y altura {h} cm. ¿Cuál es su área?",
            f"{fmt(a)} cm²", [f"{b*h} cm²", f"{fmt(Fraction(b+h,2))} cm²", f"{b+h} cm²"], BASICO, None)


def g_hipotenusa():
    a, b, c = rng.choice(TERNAS)
    k = rng.choice([1, 1, 2])
    a, b, c = a * k, b * k, c * k
    return (f"Los catetos de un triángulo rectángulo miden {a} cm y {b} cm. ¿Cuánto mide la hipotenusa?",
            f"{c} cm", [f"{a+b} cm", f"{a*a+b*b} cm", f"{abs(b-a)+c//2} cm"], INTERMEDIO, None)


def g_cateto():
    a, b, c = rng.choice(TERNAS)
    return (f"En un triángulo rectángulo la hipotenusa mide {c} m y un cateto mide {a} m. ¿Cuánto mide el otro cateto?",
            f"{b} m", [f"{c-a} m", f"{c+a} m", f"{c*c-a*a} m"], INTERMEDIO, None)


def g_area_circ():
    r = rng.randint(2, 15)
    if rng.random() < 0.5:
        return (f"¿Cuál es el área de un círculo de radio {r} cm?",
                f"{r*r}π cm²", [f"{2*r}π cm²", f"{r}π cm²", f"{4*r*r}π cm²"], INTERMEDIO, None)
    d = 2 * r
    return (f"¿Cuál es el área de un círculo cuyo diámetro mide {d} m?",
            f"{r*r}π m²", [f"{d*d}π m²", f"{d}π m²", f"{2*r*r}π m²"], INTERMEDIO, None)


def g_circunferencia():
    r = rng.randint(2, 25)
    return (f"¿Cuál es la longitud de una circunferencia de radio {r} cm?",
            f"{2*r}π cm", [f"{r*r}π cm", f"{r}π cm", f"{4*r}π cm"], BASICO, None)


def g_suma_angulos():
    n = rng.randint(5, 14)
    s = (n - 2) * 180
    return (f"¿Cuánto suman los ángulos interiores de un polígono convexo de {n} lados?",
            f"{s}°", [f"{n*180}°", f"{(n-1)*180}°", f"{360}°" if s != 360 else "540°"], INTERMEDIO, None)


def g_angulo_regular():
    n = rng.choice([5, 6, 8, 9, 10, 12, 15, 18, 20])
    ang = Fraction((n - 2) * 180, n)
    return (f"¿Cuánto mide cada ángulo interior de un polígono regular de {n} lados?",
            f"{fmt(ang)}°", [f"{fmt(Fraction(360, n))}°", f"{(n-2)*180}°", "180°", f"{fmt(ang - 15)}°"], AVANZADO, None)


def g_complemento():
    a = rng.randint(10, 80)
    if rng.random() < 0.5:
        return (f"¿Cuál es el complemento de un ángulo de {a}°?",
                f"{90-a}°", [f"{180-a}°", f"{360-a}°", f"{a}°" if a != 45 else "135°"], BASICO, None)
    return (f"¿Cuál es el suplemento de un ángulo de {a}°?",
            f"{180-a}°", [f"{90-a}°", f"{360-a}°", f"{180+a}°"], BASICO, None)


def g_vol_prisma():
    l, w, h = rng.randint(2, 12), rng.randint(2, 10), rng.randint(2, 15)
    return (f"Una caja con forma de prisma rectangular mide {l} cm × {w} cm × {h} cm. ¿Cuál es su volumen?",
            f"{l*w*h} cm³", [f"{2*(l*w+l*h+w*h)} cm³", f"{l+w+h} cm³", f"{l*w} cm³"], INTERMEDIO, None)


def g_vol_cilindro():
    r, h = rng.randint(2, 9), rng.randint(3, 20)
    return (f"Un tanque cilíndrico tiene radio {r} m y altura {h} m. ¿Cuál es su volumen?",
            f"{r*r*h}π m³", [f"{2*r*h}π m³", f"{r*h}π m³", f"{fmt(Fraction(r*r*h,3))}π m³"], AVANZADO, None)


def g_distancia():
    a, b, c = rng.choice(TERNAS[:6])
    x1, y1 = rng.randint(-6, 6), rng.randint(-6, 6)
    sx, sy = rng.choice([1, -1]), rng.choice([1, -1])
    x2, y2 = x1 + sx * a, y1 + sy * b
    return (f"¿Cuál es la distancia entre los puntos P({x1}, {y1}) y Q({x2}, {y2}) en el plano cartesiano?",
            c, [a + b, c * c, abs(a - b) + 1], AVANZADO, c)


def g_punto_medio():
    x1, y1, x2, y2 = (rng.randint(-10, 10) * 2 for _ in range(4))
    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
    return (f"Halle el punto medio del segmento con extremos A({x1}, {y1}) y B({x2}, {y2}).",
            f"({mx}, {my})", [f"({x2-x1}, {y2-y1})", f"({x1+x2}, {y1+y2})", f"({my}, {mx})" if mx != my else f"({mx+1}, {my-1})"],
            INTERMEDIO, None)


def g_pendiente():
    x1, y1 = rng.randint(-5, 5), rng.randint(-5, 5)
    x2 = x1 + rng.choice([v for v in range(-6, 7) if v != 0])
    y2 = y1 + rng.randint(-8, 8)
    m = Fraction(y2 - y1, x2 - x1)
    inv = Fraction(x2 - x1, y2 - y1) if y2 != y1 else Fraction(1, 1) + m
    return (f"¿Cuál es la pendiente de la recta que pasa por los puntos ({x1}, {y1}) y ({x2}, {y2})?",
            m, [inv, -m if m != 0 else Fraction(1, 2), m + 1], INTERMEDIO, None)


def g_tercer_angulo():
    a, b = rng.randint(20, 90), rng.randint(20, 70)
    if a + b >= 170:
        return None
    return (f"Dos ángulos de un triángulo miden {a}° y {b}°. ¿Cuánto mide el tercer ángulo?",
            f"{180-a-b}°", [f"{360-a-b}°", f"{a+b}°", f"{90-abs(a-b)}°" if 90 - abs(a - b) != 180 - a - b else f"{180-a}°"],
            BASICO, None)


def g_area_trapecio():
    B, b, h = rng.randint(8, 20), rng.randint(3, 7), rng.randint(2, 12)
    a = Fraction((B + b) * h, 2)
    return (f"Un trapecio tiene bases de {B} cm y {b} cm, y altura {h} cm. ¿Cuál es su área?",
            f"{fmt(a)} cm²", [f"{(B+b)*h} cm²", f"{B*b*h} cm²", f"{fmt(Fraction(B*h,2))} cm²"], AVANZADO, None)


GEOMETRIA = [g_area_rect, g_perim_rect, g_area_tri, g_hipotenusa, g_cateto, g_area_circ, g_circunferencia,
             g_suma_angulos, g_angulo_regular, g_complemento, g_vol_prisma, g_vol_cilindro, g_distancia,
             g_punto_medio, g_pendiente, g_tercer_angulo, g_area_trapecio]


def poly(terms):
    sup = {0: "", 1: "", 2: "²", 3: "³", 4: "⁴", 5: "⁵"}
    out = ""
    for i, (c, e) in enumerate(terms):
        if c == 0:
            continue
        sign = " − " if c < 0 else (" + " if out else "")
        if c < 0 and not out:
            sign = "−"
        ac = abs(c)
        coef = "" if (ac == 1 and e != 0) else str(ac)
        var = "" if e == 0 else "x" + sup[e]
        out += f"{sign}{coef}{var}"
    return out or "0"


def c_lineal():
    a = rng.randint(2, 9)
    x = rng.randint(-10, 12)
    b = rng.randint(-20, 20)
    c = a * x + b
    sb = f"+ {b}" if b >= 0 else f"− {abs(b)}"
    return (f"Resuelva la ecuación: {a}x {sb} = {c}",
            f"x = {x}", [f"x = {fmt(Fraction(c + b, a))}", f"x = {-x}", f"x = {c - b}", f"x = {x + 1}", f"x = {x - 2}"],
            BASICO, None)


def c_lineal2():
    a, c = rng.randint(3, 9), rng.randint(1, 2)
    x = rng.randint(-8, 10)
    b = rng.randint(-15, 15)
    d = a * x + b - c * x
    sb = f"+ {b}" if b >= 0 else f"− {abs(b)}"
    sd = f"+ {d}" if d >= 0 else f"− {abs(d)}"
    cx = "x" if c == 1 else f"{c}x"
    return (f"Halle el valor de x que satisface: {a}x {sb} = {cx} {sd}",
            f"x = {x}", [f"x = {fmt(Fraction(d - b, a + c))}", f"x = {fmt(Fraction(d + b, a - c))}", f"x = {x + 2}", f"x = {-x}", f"x = {x - 3}"],
            BASICO, None)


def c_evaluar():
    a, b, c = rng.randint(1, 5), rng.randint(-6, 6), rng.randint(-9, 9)
    x = rng.randint(-4, 4)
    v = a * x * x + b * x + c
    return (f"Si f(x) = {poly([(a,2),(b,1),(c,0)])}, ¿cuál es el valor de f({x})?",
            v, [a * x * 2 + b * x + c, -a * x * x + b * x + c, a * x * x - b * x + c], BASICO, v)


def c_raices():
    r1, r2 = rng.sample([v for v in range(-9, 10) if v != 0], 2)
    p, q = -(r1 + r2), r1 * r2
    a, b = sorted([r1, r2])
    return (f"¿Cuáles son las soluciones de la ecuación x² {'+' if p>=0 else '−'} {abs(p)}x {'+' if q>=0 else '−'} {abs(q)} = 0?",
            f"x = {a} y x = {b}", [f"x = {-b} y x = {-a}", f"x = {a} y x = {-b}" if a != -b else f"x = {a+1} y x = {b}",
                                    f"x = {p} y x = {q}"], INTERMEDIO, None)


def c_derivada_valor():
    a, b, c = rng.randint(1, 4), rng.randint(-5, 5), rng.randint(-8, 8)
    k = rng.randint(-3, 3)
    d = 3 * a * k * k + 2 * b * k + c
    f = a * k ** 3 + b * k * k + c * k
    return (f"Si f(x) = {poly([(a,3),(b,2),(c,1)])}, ¿cuál es el valor de f′({k})?",
            d, [f, 3 * a * k * k + b * k + c, a * k * k + b * k + c], AVANZADO, d)


def c_derivada_expr():
    a, n = rng.randint(2, 9), rng.randint(2, 5)
    return (f"¿Cuál es la derivada de f(x) = {poly([(a,n)])}?",
            f"f′(x) = {poly([(a*n, n-1)])}", [f"f′(x) = {poly([(a, n-1)])}", f"f′(x) = {poly([(a*n, n)])}",
                                              f"f′(x) = {poly([(n, n-1)])}" if a != 1 else "f′(x) = 0"], INTERMEDIO, None)


def c_limite_poly():
    a, b, c = rng.randint(1, 4), rng.randint(-5, 5), rng.randint(-6, 6)
    k = rng.randint(-3, 4)
    v = a * k * k + b * k + c
    return (f"Calcule el límite cuando x → {k} de {poly([(a,2),(b,1),(c,0)])}.",
            v, [v + a, "No existe", c], INTERMEDIO, v)


def c_limite_indet():
    a = rng.randint(1, 9)
    return (f"Calcule el límite cuando x → {a} de (x² − {a*a}) / (x − {a}).",
            2 * a, [a, "0", "No existe (división por cero)"], AVANZADO, 2 * a)


def c_integral():
    a, b = rng.randint(1, 6), rng.randint(0, 8)
    k = rng.randint(1, 5)
    v = Fraction(a * k * k, 2) + b * k
    return (f"Evalúe la integral definida ∫₀^{k} ({poly([(a,1),(b,0)])}) dx.",
            v, [a * k * k + b * k, a + b, Fraction(a * k, 2) + b], AVANZADO, None)


def c_potencias():
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(1, 6)
    e = a + b - c
    return (f"Simplifique la expresión (x^{a} · x^{b}) / x^{c}, con x ≠ 0.",
            f"x^{e}", [f"x^{a*b-c}", f"x^{fmt(Fraction(a*b, c))}", f"x^{a+b+c}"], BASICO, None)


def c_log():
    base = rng.choice([2, 3, 5, 10])
    k = rng.randint(2, 6 if base < 5 else 4)
    return (f"¿Cuál es el valor de log₍{base}₎({base**k})?",
            k, [base ** k // base, k + 1, base], INTERMEDIO, k)


def c_sistema():
    x, y = rng.randint(-6, 9), rng.randint(-6, 9)
    if x == y:
        return None
    s, d = x + y, x - y
    return (f"Resuelva el sistema: x + y = {s}; x − y = {d}.",
            f"x = {x}, y = {y}", [f"x = {y}, y = {x}", f"x = {s}, y = {d}", f"x = {x}, y = {-y}" if y != 0 else f"x = {x+1}, y = 1"],
            INTERMEDIO, None)


def c_composicion():
    a, b = rng.randint(2, 5), rng.randint(-5, 5)
    c = rng.randint(1, 4)
    x = rng.randint(-3, 3)
    g = x * x + c
    v = a * g + b
    sb = f"+ {b}" if b >= 0 else f"− {abs(b)}"
    return (f"Si f(x) = {a}x {sb} y g(x) = x² + {c}, ¿cuál es el valor de f(g({x}))?",
            v, [(a * x + b) ** 2 + c, a * x + b + g, v + a], INTERMEDIO, v)


def c_inecuacion():
    a = rng.randint(2, 7)
    x0 = rng.randint(-6, 8)
    b = rng.randint(-12, 12)
    c = a * x0 + b
    sb = f"+ {b}" if b >= 0 else f"− {abs(b)}"
    return (f"Resuelva la inecuación: {a}x {sb} > {c}",
            f"x > {x0}", [f"x < {x0}", f"x > {fmt(Fraction(c + b, a))}" if b != 0 else f"x > {x0+1}", f"x ≥ {x0}"],
            INTERMEDIO, None)


def c_pendiente_funcion():
    m, b = rng.choice([v for v in range(-7, 8) if v not in (0, 1)]), rng.randint(-9, 9)
    x1 = rng.randint(-3, 3)
    x2 = x1 + rng.randint(1, 4)
    tv = Fraction(m * x2 - m * x1, x2 - x1)
    return (f"¿Cuál es la tasa de variación media de f(x) = {poly([(m,1),(b,0)])} en el intervalo [{x1}, {x2}]?",
            tv, [b, m * x2 + b, -m], BASICO, None)


CALCULO = [c_lineal, c_lineal2, c_evaluar, c_raices, c_derivada_valor, c_derivada_expr, c_limite_poly,
           c_limite_indet, c_integral, c_potencias, c_log, c_sistema, c_composicion, c_inecuacion, c_pendiente_funcion]


def construir(plantillas, id_componente):
    preguntas, enunciados = [], set()
    i = 0
    intentos = 0
    while len(preguntas) < POR_COMPONENTE:
        intentos += 1
        if intentos > 20000:
            raise RuntimeError("No se pudieron generar suficientes preguntas únicas")
        t = plantillas[i % len(plantillas)]
        i += 1
        r = t()
        if r is None:
            continue
        enunciado, correcta, cand, nivel, relleno = r
        if enunciado in enunciados:
            continue
        ops, letra = opciones(correcta, cand, relleno)
        if ops is None or len(set(ops)) != 4:
            continue
        enunciados.add(enunciado)
        preguntas.append({"componente": id_componente, "nivel": nivel, "enunciado": enunciado,
                          "opciones": ops, "correcta": letra})
    return preguntas


def sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def generar():
    banco = (construir(ESTADISTICA, COMP_ESTADISTICA)
             + construir(GEOMETRIA, COMP_GEOMETRIA)
             + construir(CALCULO, COMP_CALCULO))
    preguntas, opciones = [], []
    for i, p in enumerate(banco, start=1):
        preguntas.append(f"({i}, {p['componente']}, {p['nivel']}, {sql_str(p['enunciado'])})")
        for letra, texto in zip("ABCD", p["opciones"]):
            correcta = "TRUE" if letra == p["correcta"] else "FALSE"
            opciones.append(f"({i}, '{letra}', {sql_str(texto)}, {correcta})")
    lineas = [
        "INSERT INTO preguntas (id_pregunta, id_componente, id_nivel, enunciado) VALUES",
        ",\n".join(preguntas) + ";",
        "",
        "INSERT INTO opciones_respuesta (id_pregunta, letra, texto, es_correcta) VALUES",
        ",\n".join(opciones) + ";",
        "",
        "SELECT setval(pg_get_serial_sequence('preguntas', 'id_pregunta'), (SELECT MAX(id_pregunta) FROM preguntas));",
    ]
    destino = Path(__file__).resolve().parent.parent / "database" / "03_insert_preguntas.sql"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return banco, destino


if __name__ == "__main__":
    banco, destino = generar()
    from collections import Counter
    print(f"Preguntas generadas: {len(banco)} -> {destino}")
    print("Por componente:", dict(Counter(p['componente'] for p in banco)))
    print("Por nivel:", dict(Counter(p['nivel'] for p in banco)))
    print("Distribución de la clave:", dict(Counter(p['correcta'] for p in banco)))
