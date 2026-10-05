# -*- coding: utf-8 -*-
"""生成大作业文档所需图示：用例图、时序图、模块图、ER图、流程图"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, FancyArrowPatch, Circle, Polygon, FancyBboxPatch
import matplotlib.lines as mlines
import os

plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(__file__), "figs")
os.makedirs(OUT, exist_ok=True)

EC = "#2f6f3e"      # 线条主色（深绿）
EFILL = "#f2f8ee"   # 椭圆填充
AFILL = "#fdf6e3"   # 属性填充
BOXF = "#eef4ea"    # 实体填充
FB = "#3a5f7d"      # 流程图蓝


def new_ax(w, h):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def actor(ax, x, y, label, s=1.0):
    """火柴人"""
    r = 2.2 * s
    ax.add_patch(Circle((x, y + 3.2 * s), r, fill=False, lw=1.4, ec=EC))
    ax.add_line(mlines.Line2D([x, x], [y + 1.0 * s, y - 2.6 * s], color=EC, lw=1.4))
    ax.add_line(mlines.Line2D([x - 1.8 * s, x + 1.8 * s], [y - 0.4 * s, y - 0.4 * s], color=EC, lw=1.4))
    ax.add_line(mlines.Line2D([x, x - 1.5 * s], [y - 2.6 * s, y - 5.2 * s], color=EC, lw=1.4))
    ax.add_line(mlines.Line2D([x, x + 1.5 * s], [y - 2.6 * s, y - 5.2 * s], color=EC, lw=1.4))
    ax.text(x, y - 7.6 * s, label, ha="center", va="top", fontsize=11)


def usecase(ax, x, y, w, h, text, fs=10):
    ax.add_patch(Ellipse((x, y), w, h, fill=True, fc=EFILL, ec=EC, lw=1.3))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs)


def connect(ax, x1, y1, x2, y2, ls="-"):
    ax.add_line(mlines.Line2D([x1, x2], [y1, y2], color=EC, lw=1.0, ls=ls))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


# ============ 图2.1 总体用例图 ============
def fig_overall_usecase():
    fig, ax = new_ax(11.5, 7.6)
    # 系统边界
    ax.add_patch(Rectangle((16, 4), 68, 90, fill=False, ec="#888", lw=1.3))
    ax.text(50, 96.5, "智能养殖信息管理系统", ha="center", fontsize=12.5, weight="bold")
    ucs = [
        (32, 86, "登录 / 注册"),
        (68, 86, "数据大屏 / 首页概览"),
        (32, 72, "圈舍管理"),
        (68, 72, "畜禽档案管理"),
        (32, 58, "饲喂管理"),
        (68, 58, "繁育管理"),
        (32, 44, "防疫诊疗管理"),
        (68, 44, "物资库存管理"),
        (32, 30, "销售财务管理"),
        (68, 30, "数据统计分析"),
        (32, 16, "员工与权限管理"),
        (68, 16, "系统配置管理"),
    ]
    for x, y, t in ucs:
        usecase(ax, x, y, 26, 10.5, t)
    actor(ax, 6, 78, "超级管理员")
    actor(ax, 6, 40, "养殖场主\n管理员")
    actor(ax, 94, 55, "养殖场员工")
    # 超级管理员连线
    for _, x, y, _ in [(0, 32, 86, 0), (0, 68, 86, 0), (0, 32, 16, 0), (0, 68, 16, 0)]:
        connect(ax, 8.5, 72, x - 13, y)
    # 场主连线
    for x, y in [(32, 86), (32, 72), (68, 72), (32, 58), (68, 58), (32, 44), (68, 44),
                 (32, 30), (68, 30), (32, 16), (68, 44)]:
        connect(ax, 8.5, 36, x - 13, y)
    # 员工连线
    for x, y in [(32, 86), (68, 72), (32, 58), (68, 58), (32, 44), (68, 44), (68, 30)]:
        connect(ax, 91.5, 51, x + 13, y)
    save(fig, "fig2_1_usecase_overall.png")


# ============ 图2.2 养殖场主用例图 ============
def fig_owner_usecase():
    fig, ax = new_ax(10.5, 7.8)
    ax.add_patch(Rectangle((18, 5), 72, 88, fill=False, ec="#888", lw=1.3))
    ax.text(54, 95.5, "养殖场主管理端", ha="center", fontsize=12.5, weight="bold")
    ucs = [
        (34, 85, "注册养殖场 / 登录"),
        (72, 85, "数据大屏总览"),
        (34, 72, "养殖场信息维护"),
        (72, 72, "员工账号管理"),
        (34, 59, "岗位薪资配置"),
        (72, 59, "圈舍管理"),
        (34, 46, "档案管理（入栏/转舍）"),
        (72, 46, "饲喂方案管理"),
        (34, 33, "审核中心（通过/驳回）"),
        (72, 33, "销售订单 / 成本支出"),
        (34, 20, "利润核算"),
        (72, 20, "数据统计查看"),
    ]
    for x, y, t in ucs:
        usecase(ax, x, y, 30, 10, t, fs=9.5)
    actor(ax, 7, 50, "养殖场主\n管理员")
    for x, y in [(34, 85), (72, 85), (34, 72), (72, 72), (34, 59), (72, 59),
                 (34, 46), (72, 46), (34, 33), (72, 33), (34, 20), (72, 20)]:
        connect(ax, 9.5, 46, x - 15, y)
    # include 关系：审核中心 -include-> 通知
    save(fig, "fig2_2_usecase_owner.png")


# ============ 图2.3 员工用例图 ============
def fig_staff_usecase():
    fig, ax = new_ax(10.5, 7.8)
    ax.add_patch(Rectangle((20, 5), 70, 88, fill=False, ec="#888", lw=1.3))
    ax.text(55, 95.5, "养殖场员工端", ha="center", fontsize=12.5, weight="bold")
    ucs = [
        (55, 85, "登录系统"),
        (55, 72, "查看员工工作台 / 今日任务"),
        (38, 59, "提交饲喂记录"),
        (72, 59, "登记配种 / 产犊"),
        (38, 46, "登记防疫 / 诊疗记录"),
        (72, 46, "申请物资领用"),
        (38, 33, "进货登记"),
        (72, 33, "查看繁育预警"),
        (55, 20, "查看通知公告 / 站内消息"),
    ]
    for x, y, t in ucs:
        usecase(ax, x, y, 30, 10, t, fs=9.5)
    actor(ax, 8, 58, "饲喂员")
    actor(ax, 8, 40, "繁育员")
    actor(ax, 8, 22, "兽医")
    actor(ax, 92, 40, "库管员")
    for ax_, y0 in [(10.5, 54), (10.5, 36), (10.5, 18)]:
        for x, y in [(38, 59), (72, 59), (38, 46), (72, 46), (38, 33), (72, 33), (55, 20), (55, 72), (55, 85)]:
            connect(ax, ax_, y0, x - 15, y)
    for x, y in [(38, 33), (72, 46), (38, 46), (72, 59), (55, 20)]:
        connect(ax, 89.5, 36, x + 15, y)
    save(fig, "fig2_3_usecase_staff.png")


# ============ 时序图辅助 ============
def seq_diagram(name, lifelines, msgs, w=11.5, h=6.8):
    """lifelines: [(label,x)]  msgs: [(from_x,to_x,y,label,dash)]"""
    fig, ax = new_ax(w, h)
    top = 92
    for label, x in lifelines:
        ax.add_patch(Rectangle((x - 11, top - 4), 22, 7, fill=True, fc=BOXF, ec=EC, lw=1.2))
        ax.text(x, top - 0.5, label, ha="center", va="center", fontsize=10.5)
        ax.add_line(mlines.Line2D([x, x], [top - 4, 6], color="#999", lw=1.1, ls=(0, (4, 3))))
    for x1, x2, y, label, dash in msgs:
        ls = (0, (5, 3)) if dash else "-"
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="-|>", color=FB, lw=1.4, linestyle=ls))
        ax.text((x1 + x2) / 2, y + 2.0, label, ha="center", fontsize=9.3, color="#222")
    save(fig, name)


def fig_seq_intake():
    lifelines = [("前端 (Vue 3)", 15), ("后端 API (FastAPI)", 50), ("数据库 (MySQL)", 85)]
    msgs = [
        (15, 50, 80, "提交入栏申请（品种/性别/日期）", False),
        (50, 50, 0, "", True),  # placeholder self msg skipped
        (50, 85, 71, "查询圈舍存栏与容量", False),
        (85, 50, 62, "返回可用圈舍", True),
        (50, 50, 0, "", True),
        (50, 85, 50, "写入畜禽档案（生成耳标）", False),
        (50, 85, 41, "更新圈舍当前存栏数", False),
        (85, 50, 32, "提交事务", True),
        (50, 15, 22, "返回档案信息（含耳标）", True),
        (15, 15, 0, "", True),
    ]
    msgs = [m for m in msgs if m[2] != 0]
    seq_diagram("fig2_4_seq_intake.png", lifelines, msgs, w=11.5, h=6.2)


def fig_seq_audit():
    lifelines = [("员工端前端", 13), ("后端 API", 39), ("数据库", 65), ("场主端前端", 90)]
    msgs = [
        (13, 39, 84, "提交饲喂记录", False),
        (39, 65, 75, "防重校验（同日同时段同圈舍）", False),
        (65, 39, 66, "校验结果", True),
        (39, 65, 57, "保存记录（待审核）并计算成本", False),
        (39, 90, 48, "待审核列表更新（站内消息提醒）", False),
        (90, 39, 39, "审核通过 / 驳回", False),
        (39, 65, 30, "更新审核状态（通过则联动库存）", False),
        (65, 39, 21, "返回结果", True),
        (39, 13, 12, "消息通知员工审核结果", True),
    ]
    seq_diagram("fig2_5_seq_audit.png", lifelines, msgs, w=12.5, h=6.2)


# ============ 图3.1 系统功能模块图 ============
def fig_modules():
    fig, ax = new_ax(12.5, 7.0)
    ax.set_xlim(0, 130); ax.set_ylim(0, 100)

    def box(x, y, w, h, text, fc=BOXF, fs=10.5, weight="normal", ec=EC):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0.3", fc=fc, ec=ec, lw=1.2))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight=weight)

    box(65, 92, 44, 8, "智能养殖信息管理系统", fc="#dde9d2", fs=13, weight="bold")
    l1 = [(17, "公共模块"), (48, "养殖场主模块"), (82, "养殖业务模块"), (114, "系统管理模块")]
    for x, t in l1:
        box(x, 72, 24, 7, t, fc="#e8f1df", fs=11, weight="bold")
        connect(ax, 65, 88, x, 76)
    subs = {
        17: ["登录注册", "数据大屏", "审核通知中心", "站内消息"],
        48: ["养殖场信息", "员工管理", "岗位薪资配置", "多畜种导航"],
        82: ["圈舍管理", "畜禽档案", "饲喂管理", "繁育管理", "防疫诊疗", "物资库存", "销售财务", "数据统计"],
        114: ["用户管理", "角色管理", "菜单管理", "字典管理", "日志管理", "通知公告"],
    }
    for x, items in subs.items():
        n = len(items)
        for i, it in enumerate(items):
            y = 58 - i * 11.5
            box(x, y, 21, 7.6, it, fc="white", fs=9.5)
            connect(ax, x, y + 3.8 + (3.8 if i == 0 else 0) if False else y + 3.8, x, y + 3.8)
            if i == 0:
                connect(ax, x, 68.5, x, y + 3.8)
            else:
                connect(ax, x, y + 3.8 + 11.5 - 3.8, x, y + 3.8)
    save(fig, "fig3_1_modules.png")


# ============ ER 图（Chen 表示法） ============
def er_single(name, entity, attrs, relations=None, w=9.5, h=5.6):
    """单实体 ER：中心实体 + 属性椭圆；relations: [(label, ent2)]"""
    fig, ax = new_ax(w, h)
    ex, ey = 50, 50
    ax.add_patch(Rectangle((ex - 14, ey - 5), 28, 10, fill=True, fc=BOXF, ec=EC, lw=1.4))
    ax.text(ex, ey, entity, ha="center", va="center", fontsize=12, weight="bold")
    n = len(attrs)
    import math
    for i, a in enumerate(attrs):
        ang = math.pi * (0.08 + 0.84 * i / max(n - 1, 1))
        ax_ = ex + 40 * math.cos(ang)
        ay = ey + 30 * math.sin(ang) + 12
        ax.add_patch(Ellipse((ax_, ay), 15, 8.5, fill=True, fc=AFILL, ec=EC, lw=1.1))
        ax.text(ax_, ay, a, ha="center", va="center", fontsize=9)
        connect(ax, ex + 9 * math.cos(ang), ey + 4 * math.sin(ang), ax_, ay)
    save(fig, name)


def fig_er_overall():
    fig, ax = new_ax(13.5, 8.6)
    ax.set_xlim(0, 135); ax.set_ylim(0, 100)

    def ent(x, y, text, w=20, h=8):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=True, fc=BOXF, ec=EC, lw=1.4))
        ax.text(x, y, text, ha="center", va="center", fontsize=10.5, weight="bold")

    def rel(x, y, text, w=13, h=8):
        ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                             fill=True, fc=AFILL, ec=EC, lw=1.2))
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    def rl(x1, y1, x2, y2, label="", loff=(0, 2)):
        connect(ax, x1, y1, x2, y2)
        if label:
            ax.text((x1 + x2) / 2 + loff[0], (y1 + y2) / 2 + loff[1], label, fontsize=8.6, color="#333")

    # 实体布局（3 行）
    ent(15, 88, "养殖场"); ent(50, 88, "用户"); ent(85, 88, "圈舍"); ent(120, 88, "饲喂方案")
    ent(15, 55, "畜禽档案"); ent(50, 55, "饲喂记录"); ent(85, 55, "配种记录"); ent(120, 55, "产犊记录")
    ent(15, 20, "防疫/诊疗记录"); ent(50, 20, "物资库存"); ent(85, 20, "领用记录"); ent(120, 20, "销售订单")

    rel(32.5, 88, "拥有"); rl(25, 88, 40, 88, "1", (0, 2)); rl(45, 88, 45, 88, "")
    ax.text(46, 90.2, "n", fontsize=8.6)
    rel(67.5, 88, "包含"); ax.text(56, 90.2, "1", fontsize=8.6); ax.text(77, 90.2, "n", fontsize=8.6)
    rel(102.5, 88, "制定"); ax.text(91, 90.2, "1", fontsize=8.6); ax.text(112, 90.2, "n", fontsize=8.6)

    rel(15, 71.5, "饲养"); ax.text(15, 74.2, "1", fontsize=8.6); ax.text(15, 62.4, "n", fontsize=8.6)
    rel(50, 71.5, "产生"); ax.text(50, 74.2, "n", fontsize=8.6); ax.text(50, 62.4, "1", fontsize=8.6)
    rel(102.5, 71.5, "分娩"); ax.text(102.5, 74.2, "1", fontsize=8.6); ax.text(102.5, 62.4, "n", fontsize=8.6)
    rel(67.5, 71.5, "配种"); ax.text(64, 74.2, "n", fontsize=8.6); ax.text(71, 62.4, "1", fontsize=8.6)
    # 畜禽档案-配种
    rl(25, 55, 60.5, 55, "")
    # 饲喂方案-饲喂记录
    rl(120, 84, 60, 59, "")
    ax.text(95, 76.5, "执行", fontsize=8.6)

    rel(15, 37.5, "关联"); ax.text(15, 40.2, "1", fontsize=8.6); ax.text(15, 28.4, "n", fontsize=8.6)
    rel(32.5, 37.5, "消耗")
    rl(25, 20, 40, 20, "")
    ax.text(30, 22.2, "n", fontsize=8.6); ax.text(37, 22.2, "1", fontsize=8.6)
    rel(67.5, 20, "生成"); rl(60, 20, 78.5, 20, "")
    ax.text(64, 22.2, "1", fontsize=8.6); ax.text(74, 22.2, "n", fontsize=8.6)
    rel(102.5, 37.5, "出栏")
    rl(120, 24, 102.5, 37.5, "")
    ax.text(114, 29, "n", fontsize=8.6); ax.text(107, 33.5, "1", fontsize=8.6)
    # 养殖场-物资库存 / 销售订单
    rel(32.5, 37.5, "")
    rl(25, 88, 44, 24, ""); ax.text(30, 55, "持有", fontsize=8.6, backgroundcolor="white")
    rl(25, 84, 114, 24, ""); ax.text(62, 52, "下单", fontsize=8.6, backgroundcolor="white")
    save(fig, "fig3_6_er_overall.png")


# ============ 图4.1 审核流程图 ============
def fig_audit_flow():
    fig, ax = new_ax(8.6, 10.5)

    def box(x, y, w, h, text, fc="#eef4ea"):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0.3", fc=fc, ec=EC, lw=1.3))
        ax.text(x, y, text, ha="center", va="center", fontsize=10.5)

    def diamond(x, y, w, h, text):
        ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                             fill=True, fc="#fdf6e3", ec=EC, lw=1.3))
        ax.text(x, y, text, ha="center", va="center", fontsize=10)

    def arr(x1, y1, x2, y2, label="", loff=(3, 0)):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=EC, lw=1.4))
        if label:
            ax.text((x1 + x2) / 2 + loff[0], (y1 + y2) / 2 + loff[1], label, fontsize=10)

    box(50, 95, 34, 7, "员工提交业务单据")
    arr(50, 91.5, 50, 85.5)
    box(50, 82, 40, 7, "后端校验（防重 / 库存 / 权限）")
    arr(50, 78.5, 50, 72.5)
    box(50, 69, 30, 7, "写入待审核记录")
    arr(50, 65.5, 50, 59.5)
    box(50, 56, 30, 7, "通知场主审核")
    arr(50, 52.5, 50, 46.5)
    diamond(50, 39, 30, 13, "审核是否通过？")
    arr(35, 39, 16, 39)
    ax.text(24, 41.5, "通过", fontsize=10)
    arr(65, 39, 84, 39)
    ax.text(73, 41.5, "驳回", fontsize=10)
    box(16, 26, 26, 7, "更新为审核通过")
    arr(16, 39, 16, 29.5)
    box(84, 26, 28, 7, "记录驳回原因")
    arr(84, 39, 84, 29.5)
    arr(16, 22.5, 16, 15)
    arr(84, 22.5, 84, 15)
    box(16, 11.5, 28, 7, "联动库存增减")
    box(84, 11.5, 28, 7, "站内消息通知员工")
    arr(30, 11.5, 70, 11.5)
    box(50, 3, 24, 6, "流程结束", fc="#dde9d2")
    arr(50, 8, 50, 6)
    save(fig, "fig4_1_audit_flow.png")


fig_overall_usecase()
fig_owner_usecase()
fig_staff_usecase()
fig_seq_intake()
fig_seq_audit()
fig_modules()
er_single("fig3_2_er_user.png", "用户（sys_user）",
          ["用户ID", "用户名", "密码", "真实姓名", "手机号", "用户类型", "岗位", "所属养殖场"])
er_single("fig3_3_er_animal.png", "畜禽档案（animal_archive）",
          ["档案ID", "耳标", "畜种", "品种", "性别", "出生日期", "生长阶段", "状态", "来源"])
er_single("fig3_4_er_feeding.png", "饲喂记录（feeding_record）",
          ["记录ID", "饲喂日期", "时段", "圈舍", "计划量", "实际量", "成本", "审核状态"])
er_single("fig3_5_er_mating.png", "配种记录（mating_record）",
          ["记录ID", "母畜耳标", "公畜耳标", "配种日期", "配种方式", "状态", "预产日期", "孕检结果"])
fig_er_overall()
fig_audit_flow()
print("ALL DONE")
