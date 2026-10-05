# -*- coding: utf-8 -*-
"""
生成《软件工程B》大作业插图的 draw.io 可编辑源文件（大作业插图.drawio）
包含 8 个页面：总体用例图 / 场主端用例图 / 员工端用例图 / 4 张单实体ER图 / 整体ER图
用法：python generate_drawio.py  → 输出 大作业插图.drawio
用 https://app.diagrams.net 或 draw.io 桌面版打开即可拖拽编辑，导出 PNG 时建议缩放 200%
"""
from xml.sax.saxutils import escape

ST_ELLIPSE = "ellipse;whiteSpace=wrap;html=1;fillColor=#f2f8ee;strokeColor=#2f6f3e;fontSize=14;"
ST_ATTR = "ellipse;whiteSpace=wrap;html=1;fillColor=#fdf6e3;strokeColor=#2f6f3e;fontSize=13;"
ST_ENTITY = "rounded=0;whiteSpace=wrap;html=1;fillColor=#eef4ea;strokeColor=#2f6f3e;fontSize=14;fontStyle=1;"
ST_RHOMBUS = "rhombus;whiteSpace=wrap;html=1;fillColor=#fdf6e3;strokeColor=#2f6f3e;fontSize=13;"
ST_ACTOR = "shape=umlActor;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;verticalAlign=top;html=1;outlineConnect=0;fontSize=14;"
ST_BOUNDARY = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#999999;verticalAlign=top;fontSize=15;fontStyle=1;"
ST_EDGE = "edgeStyle=none;rounded=0;html=1;endArrow=none;strokeColor=#2f6f3e;strokeWidth=1.5;"
ST_TEXT = "text;html=1;align=center;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#555555;"


class Page:
    def __init__(self, name):
        self.name = name
        self.cells = []
        self._id = 1

    def nid(self):
        self._id += 1
        return f"n{self._id}"

    def vertex(self, x, y, w, h, label, style):
        cid = self.nid()
        self.cells.append(
            f'<mxCell id="{cid}" value="{escape(label)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        return cid

    def edge(self, src, dst):
        cid = self.nid()
        self.cells.append(
            f'<mxCell id="{cid}" value="" style="{ST_EDGE}" edge="1" parent="1" '
            f'source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )
        return cid

    def text(self, x, y, label):
        return self.vertex(x, y, 30, 20, label, ST_TEXT)

    def xml(self):
        body = "\n".join(self.cells)
        return f'''      <mxGraphModel dx="1200" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1150" pageHeight="850" math="0" shadow="0">
        <root>
          <mxCell id="0"/>
          <mxCell id="1" parent="0"/>
{body}
        </root>
      </mxGraphModel>'''


def ellipse(page, cx, cy, w, h, label, style=ST_ELLIPSE):
    return page.vertex(int(cx - w / 2), int(cy - h / 2), w, h, label, style)


# ============ 1 总体用例图 ============
def page_overall_usecase():
    p = Page("总体用例图")
    p.vertex(170, 30, 520, 590, "智能养殖信息管理系统", ST_BOUNDARY)
    ucs = [
        ("登录 / 注册", 250, 80), ("数据大屏 / 首页概览", 610, 80),
        ("圈舍管理", 250, 170), ("畜禽档案管理", 610, 170),
        ("饲喂管理", 250, 260), ("繁育管理", 610, 260),
        ("防疫诊疗管理", 250, 350), ("物资库存管理", 610, 350),
        ("销售财务管理", 250, 440), ("数据统计分析", 610, 440),
        ("员工与权限管理", 250, 540), ("系统配置管理", 610, 540),
    ]
    ids = {}
    for label, cx, cy in ucs:
        ids[label] = ellipse(p, cx, cy, 165, 55, label)
    a_super = p.vertex(60, 120, 45, 60, "超级管理员", ST_ACTOR)
    a_owner = p.vertex(60, 400, 45, 60, "养殖场主管理员", ST_ACTOR)
    a_staff = p.vertex(770, 330, 45, 60, "养殖场员工", ST_ACTOR)
    for t in ["登录 / 注册", "数据大屏 / 首页概览", "员工与权限管理", "系统配置管理"]:
        p.edge(a_super, ids[t])
    for label, cx, cy in ucs:
        p.edge(a_owner, ids[label])
    for t in ["登录 / 注册", "畜禽档案管理", "饲喂管理", "繁育管理",
              "防疫诊疗管理", "物资库存管理", "数据统计分析"]:
        p.edge(a_staff, ids[t])
    return p


# ============ 2 场主端用例图 ============
def page_owner_usecase():
    p = Page("养殖场主管理端用例图")
    p.vertex(150, 30, 570, 590, "养殖场主管理端", ST_BOUNDARY)
    ucs = [
        ("注册养殖场 / 登录", 260, 80), ("数据大屏总览", 610, 80),
        ("养殖场信息维护", 260, 170), ("员工账号管理", 610, 170),
        ("岗位薪资配置", 260, 260), ("圈舍管理", 610, 260),
        ("档案管理（入栏/转舍）", 260, 350), ("饲喂方案管理", 610, 350),
        ("审核中心（通过/驳回）", 260, 440), ("销售订单 / 成本支出", 610, 440),
        ("利润核算", 260, 540), ("数据统计查看", 610, 540),
    ]
    a = p.vertex(55, 330, 45, 60, "养殖场主管理员", ST_ACTOR)
    for label, cx, cy in ucs:
        p.edge(a, ellipse(p, cx, cy, 200, 55, label))
    return p


# ============ 3 员工端用例图 ============
def page_staff_usecase():
    p = Page("养殖场员工端用例图")
    p.vertex(160, 30, 540, 610, "养殖场员工端", ST_BOUNDARY)
    uc_login = ellipse(p, 430, 85, 200, 55, "登录系统")
    uc_bench = ellipse(p, 430, 175, 230, 55, "查看工作台 / 今日任务")
    uc_feed = ellipse(p, 285, 285, 190, 55, "提交饲喂记录")
    uc_breed = ellipse(p, 590, 285, 190, 55, "登记配种 / 产犊")
    uc_health = ellipse(p, 285, 375, 190, 55, "登记防疫 / 诊疗")
    uc_alert = ellipse(p, 590, 375, 190, 55, "查看繁育预警")
    uc_purchase = ellipse(p, 285, 465, 190, 55, "进货登记")
    uc_consume = ellipse(p, 590, 465, 190, 55, "申请物资领用")
    uc_notice = ellipse(p, 430, 575, 240, 55, "查看通知 / 站内消息")
    a_feeder = p.vertex(50, 240, 45, 60, "饲喂员", ST_ACTOR)
    a_breeder = p.vertex(50, 350, 45, 60, "繁育员", ST_ACTOR)
    a_vet = p.vertex(50, 470, 45, 60, "兽医", ST_ACTOR)
    a_keeper = p.vertex(790, 350, 45, 60, "库管员", ST_ACTOR)
    conns = {
        a_feeder: [uc_login, uc_bench, uc_feed, uc_purchase, uc_notice],
        a_breeder: [uc_login, uc_bench, uc_breed, uc_alert, uc_notice],
        a_vet: [uc_login, uc_bench, uc_health, uc_consume, uc_notice],
        a_keeper: [uc_login, uc_bench, uc_purchase, uc_consume, uc_notice],
    }
    for a, ts in conns.items():
        for t in ts:
            p.edge(a, t)
    return p


# ============ 4-7 单实体 ER ============
def page_er_single(name, entity, attrs):
    p = Page(name)
    cx, cy = 430, 330
    e = p.vertex(cx - 90, cy - 35, 180, 70, entity, ST_ENTITY)
    import math
    n = len(attrs)
    rx, ry = 315, 225
    for i, a in enumerate(attrs):
        ang = 2 * math.pi * i / n + math.pi / n
        ax, ay = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        aid = ellipse(p, ax, ay, 135, 50, a, ST_ATTR)
        p.edge(e, aid)
    return p


# ============ 8 整体 ER ============
def page_er_overall():
    p = Page("系统整体ER图")
    EW, EH, DW, DH = 150, 56, 120, 70
    ents = {}
    pos = {
        "用户": (80, 60), "养殖场": (400, 60), "圈舍": (720, 60), "防疫/诊疗": (1000, 60),
        "领用记录": (80, 380), "饲喂记录": (400, 380), "畜禽档案": (720, 380), "饲喂方案": (1000, 380),
        "物资库存": (80, 700), "销售订单": (400, 700), "配种记录": (720, 700), "产犊记录": (1000, 700),
    }
    for k, (x, y) in pos.items():
        ents[k] = p.vertex(x - EW / 2, y - EH / 2, EW, EH, k, ST_ENTITY)

    def rel(label, cx, cy):
        return p.vertex(cx - DW / 2, cy - DH / 2, DW, DH, label, ST_RHOMBUS)

    def card(x, y, t):
        p.text(x, y, t)

    r_own = rel("拥有", 240, 60);  p.edge(ents["用户"], r_own);  p.edge(r_own, ents["养殖场"])
    card(150, 30, "n"); card(320, 30, "1")
    r_contain = rel("包含", 560, 60); p.edge(ents["养殖场"], r_contain); p.edge(r_contain, ents["圈舍"])
    card(480, 30, "1"); card(640, 30, "n")
    r_hold = rel("容纳", 720, 220); p.edge(ents["圈舍"], r_hold); p.edge(r_hold, ents["畜禽档案"])
    card(735, 130, "1"); card(735, 300, "n")
    r_gen = rel("产生", 560, 380); p.edge(ents["畜禽档案"], r_gen); p.edge(r_gen, ents["饲喂记录"])
    card(645, 350, "1"); card(480, 350, "n")
    r_mate = rel("配种", 720, 540); p.edge(ents["畜禽档案"], r_mate); p.edge(r_mate, ents["配种记录"])
    card(735, 450, "1"); card(735, 620, "n")
    r_birth = rel("分娩", 860, 700); p.edge(ents["配种记录"], r_birth); p.edge(r_birth, ents["产犊记录"])
    card(790, 672, "1"); card(930, 672, "n")
    r_exec = rel("执行", 1000, 220); p.edge(ents["饲喂方案"], r_exec)
    card(1015, 130, "1")
    # 执行 → 饲喂记录（自动折线，用户可拖动调整）
    e_exec = p.nid()
    p.cells.append(
        f'<mxCell id="{e_exec}" value="" style="{ST_EDGE}" edge="1" parent="1" '
        f'source="{r_exec}" target="{ents["饲喂记录"]}">'
        f'<mxGeometry relative="1" as="geometry"><Array as="points">'
        f'<mxPoint x="1000" y="470"/><mxPoint x="400" y="470"/>'
        f'</Array></mxGeometry></mxCell>')
    card(960, 440, "n")
    r_asso = rel("关联", 880, 170); p.edge(ents["防疫/诊疗"], r_asso); p.edge(r_asso, ents["畜禽档案"])
    card(960, 100, "n"); card(800, 260, "1")
    r_possess = rel("持有", 240, 220); p.edge(ents["养殖场"], r_possess); p.edge(r_possess, ents["物资库存"])
    card(330, 130, "1"); card(160, 620, "n")
    r_produce = rel("生成", 80, 540); p.edge(ents["物资库存"], r_produce); p.edge(r_produce, ents["领用记录"])
    card(95, 620, "1"); card(95, 450, "n")
    r_out = rel("出栏", 560, 540); p.edge(ents["销售订单"], r_out); p.edge(r_out, ents["畜禽档案"])
    card(480, 620, "m"); card(640, 450, "n")
    return p


pages = [
    page_overall_usecase(),
    page_owner_usecase(),
    page_staff_usecase(),
    page_er_single("ER-用户", "用户 sys_user",
                   ["用户ID（主键）", "用户名", "密码", "真实姓名", "手机号", "用户类型", "岗位", "所属养殖场"]),
    page_er_single("ER-畜禽档案", "畜禽档案 animal_archive",
                   ["档案ID（主键）", "耳标", "畜种", "品种", "性别", "出生日期", "生长阶段", "状态", "来源"]),
    page_er_single("ER-饲喂记录", "饲喂记录 feeding_record",
                   ["记录ID（主键）", "饲喂日期", "时段", "圈舍", "计划量", "实际量", "成本", "审核状态"]),
    page_er_single("ER-配种记录", "配种记录 mating_record",
                   ["记录ID（主键）", "母畜耳标", "公畜耳标", "配种日期", "配种方式", "状态", "预产日期", "孕检结果"]),
    page_er_overall(),
]

diagrams = []
for i, pg in enumerate(pages, 1):
    diagrams.append(
        f'  <diagram id="page{i}" name="{escape(pg.name)}">\n{pg.xml()}\n  </diagram>'
    )

mxfile = '<mxfile host="app.diagrams.net" agent="ZCode" version="21.0.0" type="device">\n' + "\n".join(diagrams) + "\n</mxfile>\n"
out = "大作业插图.drawio"
with open(out, "w", encoding="utf-8") as f:
    f.write(mxfile)
print("written", out, len(mxfile), "chars,", len(pages), "pages")
