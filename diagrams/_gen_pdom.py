#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор PDOM «МедЭксперт» (групповой проект, ЛР1 — каркас).
Раскладка отражает клиент-серверную структуру: АРМВрача (много) сверху,
серверные модули-одиночки ниже, объекты данных в центре, ресурсы по краям.
Чёрно-белое исполнение (белый фон, чёрные линии и текст).
Перед сохранением — самопроверка геометрии (перекрытия боксов, линии сквозь
чужие боксы) и PNG-превью."""
import os
import xml.etree.ElementTree as ET

OUT = os.path.dirname(os.path.abspath(__file__))
RH = 22  # высота строки класса

_id = [1]
def nid():
    _id[0] += 1
    return f"n{_id[0]}"

def box_h(n_rows):
    return 30 + RH * n_rows + 2

# Единый ч/б стиль для всех типов сущностей
KIND_STYLE = {k: "fillColor=#FFFFFF;strokeColor=#000000;fontColor=#000000;" for k in
              ("класс", "объект", "ресурс", "внешний", "роль")}

# ── Раскладка: имя -> (x, y, w, атрибуты, тип) ────────────────────────────────
CLASSES = {
    # верх: клиент
    "АРМВрача":                 (700,  60,  240, [], "класс"),
    # второй ряд: серверные модули + внешний аптечный сервис
    "МодульРегистрации":        (180,  210, 220, [], "класс"),
    "МодульДиагностики":        (620,  210, 220, [], "класс"),
    "МодульЛечения":            (1060, 210, 220, [], "класс"),
    "АптечныйСервис":           (1560, 210, 200, [], "внешний"),
    # третий ряд: объекты данных (конвейер обследование → диагноз → план)
    "Медкарта":                 (180,  400, 210, ["ФИО пациента", "дата рождения", "пол",
                                                  "номер полиса", "хронические заболевания",
                                                  "аллергии"], "объект"),
    "Обследование":             (620,  400, 210, ["дата", "статус"], "объект"),
    "ПредварительныйДиагноз":   (990,  400, 240, ["название болезни", "обоснование",
                                                  "уверенность", "статус"], "объект"),
    "ПланЛечения":              (1320, 400, 200, ["срок", "рекомендации", "статус"], "объект"),
    # низ: внешняя МИС, части обследования, хранилище, препараты
    "ВнешняяМИС":               (60,   640, 190, [], "внешний"),
    "Анамнез":                  (460,  640, 190, ["жалобы", "симптомы", "давность",
                                                  "комментарии врача"], "объект"),
    "ПоказаниеПрибора":         (760,  640, 200, ["тип прибора", "показатель", "значение",
                                                  "единицы", "флаг отклонения"], "объект"),
    "БДОбследований":           (1060, 640, 200, [], "ресурс"),
    "Препарат":                 (1400, 640, 190, ["название", "дозировка", "форма выпуска",
                                                  "наличие"], "объект"),
}

# ── Рёбра: (src, dst, имя, кратность_src, кратность_dst, exit(x,y), entry(x,y), waypoints) ──
EDGES = [
    # клиент → серверные модули («много клиентов — один обработчик»)
    ("АРМВрача", "МодульРегистрации", "отправляет данные обследования", "0..*", "1",
     (0, 0.5), (0.5, 0), [(290, 76)]),
    ("АРМВрача", "МодульДиагностики", "запрашивает гипотезы", "0..*", "1",
     (0.33, 1), (0.5, 0), [(780, 150), (730, 150)]),
    ("АРМВрача", "МодульЛечения", "запрашивает план лечения", "0..*", "1",
     (1, 0.5), (0.5, 0), [(1170, 76)]),
    # модули формируют объекты
    ("МодульРегистрации", "Обследование", "формирует", "1", "0..*",
     (0.5, 1), (0.5, 0), [(290, 330), (725, 330)]),
    ("МодульДиагностики", "ПредварительныйДиагноз", "формирует", "1", "0..*",
     (0.5, 1), (0.5, 0), [(730, 340), (1110, 340)]),
    ("МодульЛечения", "ПланЛечения", "формирует", "1", "0..*",
     (0.5, 1), (0.5, 0), [(1170, 340), (1420, 340)]),
    # конвейер данных
    ("Обследование", "Медкарта", "оформляется по", "0..*", "1",
     (0, 0.5), (1, 0.5), [(505, 438), (505, 482)]),
    ("Обследование", "Анамнез", "содержит", "1", "1",
     (0.25, 1), (0.5, 0), [(672, 580), (555, 580)]),
    ("Обследование", "ПоказаниеПрибора", "содержит", "1", "1..*",
     (0.75, 1), (0.5, 0), [(778, 580), (860, 580)]),
    ("ПредварительныйДиагноз", "Обследование", "ставится по", "0..*", "1",
     (0.25, 0), (0.9, 0), [(1050, 370), (809, 370)]),
    ("ПланЛечения", "ПредварительныйДиагноз", "составляется по", "1", "1",
     (0, 0.5), (1, 0.5), [(1255, 449), (1255, 460)]),
    ("ПланЛечения", "Препарат", "включает", "1", "0..*",
     (0.5, 1), (0.5, 0), [(1420, 570), (1495, 570)]),
    # ресурсы и внешние системы
    ("БДОбследований", "Обследование", "хранит", "1", "0..*",
     (0.2, 0), (1, 0.9), [(1100, 580), (935, 580), (935, 468)]),
    ("ВнешняяМИС", "Медкарта", "предоставляет", "1", "0..*",
     (0.5, 0), (0.3, 1), [(155, 600), (243, 600)]),
    ("АптечныйСервис", "Препарат", "предоставляет наличие", "1", "0..*",
     (0.5, 1), (1, 0.5), [(1655, 700)]),
]

# Тип связи: ассоциация (стрелка) / агрегация (пустой ромб у владельца) /
# композиция (закрашенный ромб у владельца)
DEP_KIND = {
    ("Обследование", "Анамнез"): "comp",
    ("Обследование", "ПоказаниеПрибора"): "comp",
    ("БДОбследований", "Обследование"): "aggr",
    ("ПланЛечения", "Препарат"): "aggr",
}

# Явные позиции подписей рёбер в превью (когда автопозиция прячется за бокс)
LABEL_POS = {
    ("ПланЛечения", "ПредварительныйДиагноз"): (1255, 545),
}


def rect(name):
    x, y, w, attrs, _ = CLASSES[name]
    return (x, y, x + w, y + box_h(len(attrs)))


def anchors(src, dst, exit_a, entry_a):
    (sx1, sy1, sx2, sy2) = rect(src)
    (dx1, dy1, dx2, dy2) = rect(dst)
    ex = (sx1 + (sx2 - sx1) * exit_a[0], sy1 + (sy2 - sy1) * exit_a[1])
    en = (dx1 + (dx2 - dx1) * entry_a[0], dy1 + (dy2 - dy1) * entry_a[1])
    return ex, en


def seg_box_intersect(p, q, box, pad=2):
    """Пересекается ли отрезок p-q с прямоугольником box (с отступом pad)."""
    bx1, by1, bx2, by2 = box
    bx1, by1, bx2, by2 = bx1 - pad, by1 - pad, bx2 + pad, by2 + pad

    def inside(pt):
        return bx1 <= pt[0] <= bx2 and by1 <= pt[1] <= by2

    if inside(p) or inside(q):
        return True
    def segs_intersect(a, b, c, d):
        def ccw(A, B, C):
            return (C[1]-A[1])*(B[0]-A[0]) > (B[1]-A[1])*(B[0]-A[0])
        return ccw(a,c,d) != ccw(b,c,d) and ccw(a,b,c) != ccw(a,b,d)
    corners = [(bx1,by1),(bx2,by1),(bx2,by2),(bx1,by2)]
    for i in range(4):
        if segs_intersect(p, q, corners[i], corners[(i+1) % 4]):
            return True
    return False


def check_geometry():
    problems = []
    names = list(CLASSES)
    # 1. Перекрытие боксов
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = rect(names[i]), rect(names[j])
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                problems.append(f"ПЕРЕКРЫТИЕ боксов: {names[i]} × {names[j]}")
    # 2. Линии сквозь чужие боксы
    for src, dst, label, _, _, exit_a, entry_a, wps in EDGES:
        ex, en = anchors(src, dst, exit_a, entry_a)
        pts = [ex] + list(wps) + [en]
        for k in range(len(pts) - 1):
            for nm in names:
                if nm in (src, dst):
                    continue
                if seg_box_intersect(pts[k], pts[k + 1], rect(nm)):
                    problems.append(f"ЛИНИЯ {src}--{dst} ({label}) проходит сквозь {nm}")
    return problems


# Смещение контента, чтобы он лежал по центру страницы drawio
OX, OY = 30, 45
PAGE_W, PAGE_H = 1850, 950

def gen_drawio():
    mx = ET.Element("mxfile", host="app.diagrams.net", version="24.7.5")
    d = ET.SubElement(mx, "diagram", id=nid(), name="PDOM — МедЭксперт")
    gm = ET.SubElement(d, "mxGraphModel", dx="800", dy="600", grid="1", gridSize="10", guides="1",
                       tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                       pageWidth=str(PAGE_W), pageHeight=str(PAGE_H), math="0", shadow="0")
    root = ET.SubElement(gm, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # заголовок
    t = ET.Element("mxCell", id=nid(),
                   value="ПС «МедЭксперт» — объектная модель предметной области (PDOM)",
                   style="text;html=1;fontSize=18;fontStyle=1;", vertex="1", parent="1")
    ET.SubElement(t, "mxGeometry", x=str(60 + OX), y=str(OY), width="900", height="30", **{'as': 'geometry'})
    root.append(t)

    ids = {}
    row_st = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;spacingRight=4;"
              "overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;")
    for name, (x, y, w, attrs, kind) in CLASSES.items():
        i = nid()
        st = ("swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;"
              "startSize=30;horizontalStack=0;resizeParent=1;resizeParentMax=0;collapsible=1;marginBottom=0;"
              "whiteSpace=wrap;html=1;" + KIND_STYLE[kind])
        c = ET.Element("mxCell", id=i, value=name, style=st, vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(x + OX), y=str(y + OY), width=str(w),
                      height=str(box_h(len(attrs))), **{'as': 'geometry'})
        root.append(c)
        ids[name] = i
        prev = i
        for k, txt in enumerate(attrs):
            rid = nid()
            rc = ET.Element("mxCell", id=rid, value=txt, style=row_st, vertex="1", parent=prev)
            ET.SubElement(rc, "mxGeometry", y=str(30 + k * RH),
                          width=str(w), height=str(RH), **{'as': 'geometry'})
            root.append(rc)
            prev = rid

    for src, dst, label, m1, m2, exit_a, entry_a, wps in EDGES:
        e = nid()
        kind = DEP_KIND.get((src, dst), "assoc")
        arrow = {"assoc": "endArrow=open;",
                 "aggr":  "startArrow=aggregation;startFill=0;endArrow=open;",
                 "comp":  "startArrow=composition;startFill=1;endArrow=open;"}[kind]
        st = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;fontColor=#000000;{arrow}"
              f"exitX={exit_a[0]};exitY={exit_a[1]};exitDx=0;exitDy=0;"
              f"entryX={entry_a[0]};entryY={entry_a[1]};entryDx=0;entryDy=0;")
        ec = ET.Element("mxCell", id=e, value="", style=st, edge="1", parent="1",
                        source=ids[src], target=ids[dst])
        g = ET.SubElement(ec, "mxGeometry", relative="1", **{'as': 'geometry'})
        if wps:
            arr = ET.SubElement(g, "Array", **{'as': 'points'})
            for (px, py) in wps:
                ET.SubElement(arr, "mxPoint", x=str(px + OX), y=str(py + OY))
        for txt, gx in ((label[0].upper() + label[1:], 0), (m1, -1), (m2, 1)):
            lb = ET.SubElement(ec, "mxCell", id=nid(), value=txt,
                               style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;fontColor=#000000;",
                               vertex="1", connectable="0")
            ET.SubElement(lb, "mxGeometry", x=str(gx), y="0", relative="1", **{'as': 'geometry'})
        root.append(ec)

    ET.indent(mx, space="  ")
    ET.ElementTree(mx).write(os.path.join(OUT, "медэксперт-pdom.drawio"),
                             encoding="utf-8", xml_declaration=True)


def gen_preview():
    """PNG-превью средствами PIL (прокси для визуальной проверки)."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except OSError:
        font = font_b = ImageFont.load_default()
    max_x = max(rect(n)[2] for n in CLASSES) + 60
    max_y = max(rect(n)[3] for n in CLASSES) + 80
    img = Image.new("RGB", (max_x, max_y), "white")
    dr = ImageDraw.Draw(img)
    def text_bg(pos, txt, font, fill, anchor=None):
        """Текст с белой подложкой, чтобы читался поверх линий."""
        x, y = pos
        bb = dr.textbbox((x, y), txt, font=font, anchor=anchor)
        dr.rectangle([bb[0]-1, bb[1]-1, bb[2]+1, bb[3]+1], fill="white")
        dr.text((x, y), txt, fill=fill, font=font, anchor=anchor)

    def mult_label(pt, ax, ay, txt):
        """Кратность у конца ребра — со сдвигом НАРУЖУ от бокса."""
        x, y = pt
        if ay == 0:        # верхняя кромка — подпись над линией
            text_bg((x, y - 10), txt, font, "#000000", anchor="ms")
        elif ay == 1:      # нижняя кромка — под линией
            text_bg((x, y + 10), txt, font, "#000000", anchor="ms")
        elif ax == 0:      # левая кромка — слева от точки
            text_bg((x - 5, y), txt, font, "#000000", anchor="rm")
        else:              # правая кромка — справа от точки
            text_bg((x + 5, y), txt, font, "#000000", anchor="lm")

    # 1) боксы (линии потом лягут поверх пустых зон, подписи — поверх всего)
    for name, (x, y, w, attrs, kind) in CLASSES.items():
        x, y = x + OX, y + OY
        h = box_h(len(attrs))
        dr.rectangle([x, y, x + w, y + h], fill="#FFFFFF", outline="#000000", width=2)
        dr.line([x, y + 30, x + w, y + 30], fill="black", width=2)
        dr.text((x + w / 2, y + 8), name, fill="black", font=font_b, anchor="ma")
        yy = y + 30
        for row in attrs:
            dr.text((x + 6, yy + 3), row, fill="black", font=font)
            yy += RH

    # 2) рёбра
    for src, dst, label, m1, m2, exit_a, entry_a, wps in EDGES:
        ex, en = anchors(src, dst, exit_a, entry_a)
        ex, en = (ex[0] + OX, ex[1] + OY), (en[0] + OX, en[1] + OY)
        pts = [ex] + [(px + OX, py + OY) for (px, py) in wps] + [en]
        dr.line(pts, fill="black", width=2)
        kind = DEP_KIND.get((src, dst), "assoc")
        arrow_head(dr, pts[-2], pts[-1])
        if kind == "comp":
            diamond(dr, pts[0], pts[1], filled=True)
        elif kind == "aggr":
            diamond(dr, pts[0], pts[1], filled=False)
        mult_label(ex, exit_a[0], exit_a[1], m1)
        mult_label(en, entry_a[0], entry_a[1], m2)

    # 3) подписи рёбер — центр самого длинного сегмента (или явная позиция)
    for src, dst, label, m1, m2, exit_a, entry_a, wps in EDGES:
        ex, en = anchors(src, dst, exit_a, entry_a)
        ex, en = (ex[0] + OX, ex[1] + OY), (en[0] + OX, en[1] + OY)
        pts = [ex] + [(px + OX, py + OY) for (px, py) in wps] + [en]
        segs = [(pts[k], pts[k+1]) for k in range(len(pts)-1)]
        a, b = max(segs, key=lambda s: abs(s[1][0]-s[0][0]) + abs(s[1][1]-s[0][1]))
        mx_, my_ = (a[0]+b[0])/2, (a[1]+b[1])/2
        if (src, dst) in LABEL_POS:
            mx_, my_ = LABEL_POS[(src, dst)][0] + OX, LABEL_POS[(src, dst)][1] + OY
        text_bg((mx_, my_ - 16), label[0].upper() + label[1:], font, "#000000", anchor="mm")

    img.save(os.path.join(OUT, "медэксперт-pdom-превью.png"))
    print(f"превью: медэксперт-pdom-превью.png ({max_x}x{max_y})")


def arrow_head(dr, p_from, p_to):
    """Открытая стрелка у конца ребра (по направлению последнего сегмента)."""
    import math
    dx, dy = p_to[0] - p_from[0], p_to[1] - p_from[1]
    L = math.hypot(dx, dy)
    if L == 0:
        return
    ux, uy = dx / L, dy / L
    b = (p_to[0] - ux * 11, p_to[1] - uy * 11)
    px, py = -uy, ux
    dr.line([p_to, (b[0] + px * 4.5, b[1] + py * 4.5)], fill="black", width=2)
    dr.line([p_to, (b[0] - px * 4.5, b[1] - py * 4.5)], fill="black", width=2)


def diamond(dr, at, toward, filled):
    """Ромб владения у начала ребра (at — у края бокса-владельца)."""
    import math
    dx, dy = toward[0] - at[0], toward[1] - at[1]
    L = math.hypot(dx, dy)
    if L == 0:
        return
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    s, w = 20, 11
    pts = [at,
           (at[0] + ux * s + px * w, at[1] + uy * s + py * w),
           (at[0] + ux * 2 * s, at[1] + uy * 2 * s),
           (at[0] + ux * s - px * w, at[1] + uy * s - py * w)]
    dr.polygon(pts, fill="black" if filled else "white", outline="black", width=2)


if __name__ == "__main__":
    problems = check_geometry()
    for p in problems:
        print("!!", p)
    if problems:
        raise SystemExit("геометрия грязная — правь раскладку")
    gen_drawio()
    gen_preview()
    print("OK: медэксперт-pdom.drawio перегенерирован, геометрия чистая")
